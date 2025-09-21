import json
import asyncio
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Request
from loguru import logger

from services.redis_service import RedisService


router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Map of request_id to set of connected WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, request_id: str):
        """Connect a WebSocket for a specific analysis request"""
        await websocket.accept()
        
        if request_id not in self.active_connections:
            self.active_connections[request_id] = set()
        
        self.active_connections[request_id].add(websocket)
        
        logger.info(f"WebSocket connected for analysis {request_id}")
    
    def disconnect(self, websocket: WebSocket, request_id: str):
        """Disconnect a WebSocket"""
        if request_id in self.active_connections:
            self.active_connections[request_id].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[request_id]:
                del self.active_connections[request_id]
        
        logger.info(f"WebSocket disconnected for analysis {request_id}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.warning(f"Failed to send message to WebSocket: {e}")
    
    async def broadcast_to_analysis(self, message: dict, request_id: str):
        """Broadcast a message to all WebSockets connected to a specific analysis"""
        if request_id not in self.active_connections:
            return
        
        disconnected_sockets = set()
        
        for websocket in self.active_connections[request_id].copy():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to send message, marking for disconnection: {e}")
                disconnected_sockets.add(websocket)
        
        # Clean up disconnected sockets
        for websocket in disconnected_sockets:
            self.disconnect(websocket, request_id)


# Global connection manager
manager = ConnectionManager()


def get_redis_service(request: Request) -> RedisService:
    """Dependency to get Redis service from app state"""
    return request.app.state.redis_service


@router.websocket("/analysis/{request_id}")
async def websocket_analysis_updates(
    websocket: WebSocket, 
    request_id: str
):
    """
    WebSocket endpoint for real-time analysis updates
    
    Connects to a specific analysis and receives real-time updates about:
    - Progress changes
    - Stage transitions
    - Errors and warnings
    - Completion status
    """
    await manager.connect(websocket, request_id)
    
    # Get Redis service from the app state (accessed through the WebSocket's scope)
    redis_service = websocket.scope['app'].state.redis_service
    
    try:
        # Send initial status
        initial_status = await get_current_analysis_status(request_id, redis_service)
        if initial_status:
            await manager.send_personal_message(initial_status, websocket)
        
        # Start monitoring for updates
        monitoring_task = asyncio.create_task(
            monitor_analysis_progress(request_id, redis_service)
        )
        
        # Keep connection alive and handle incoming messages
        try:
            while True:
                # Wait for messages from client (like ping/pong)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await manager.send_personal_message(
                        {"type": "pong", "timestamp": asyncio.get_event_loop().time()},
                        websocket
                    )
                elif message.get("type") == "get_status":
                    # Send current status on demand
                    current_status = await get_current_analysis_status(request_id, redis_service)
                    if current_status:
                        await manager.send_personal_message(current_status, websocket)
                
        except WebSocketDisconnect:
            pass
        finally:
            monitoring_task.cancel()
            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass
    
    except Exception as e:
        logger.error(f"WebSocket error for analysis {request_id}: {e}")
    
    finally:
        manager.disconnect(websocket, request_id)


async def monitor_analysis_progress(request_id: str, redis_service: RedisService):
    """Monitor analysis progress and broadcast updates"""
    last_progress = -1
    last_stage = ""
    
    try:
        while True:
            # Get current progress from Redis
            progress_data = await redis_service.get_analysis_progress(request_id)
            
            if progress_data:
                current_progress = progress_data.get("progress", 0)
                current_stage = progress_data.get("current_stage", "")
                status = progress_data.get("status", "unknown")
                
                # Check if there's an update to broadcast
                if (current_progress != last_progress or 
                    current_stage != last_stage):
                    
                    update_message = {
                        "type": "progress_update",
                        "request_id": request_id,
                        "progress": current_progress,
                        "stage": current_stage,
                        "status": status,
                        "timestamp": progress_data.get("updated_at")
                    }
                    
                    await manager.broadcast_to_analysis(update_message, request_id)
                    
                    last_progress = current_progress
                    last_stage = current_stage
                
                # If completed or failed, send final status and break
                if status in ["completed", "failed"]:
                    final_message = {
                        "type": "analysis_complete",
                        "request_id": request_id,
                        "status": status,
                        "progress": 100,
                        "timestamp": progress_data.get("updated_at")
                    }
                    
                    await manager.broadcast_to_analysis(final_message, request_id)
                    break
            
            # Wait before next check
            await asyncio.sleep(2)  # Check every 2 seconds
    
    except asyncio.CancelledError:
        # Task was cancelled, exit gracefully
        pass
    except Exception as e:
        logger.error(f"Error monitoring progress for {request_id}: {e}")


async def get_current_analysis_status(request_id: str, redis_service: RedisService) -> dict:
    """Get the current analysis status from Redis"""
    try:
        # Try to get from analysis progress first
        progress_data = await redis_service.get_analysis_progress(request_id)
        
        if progress_data:
            return {
                "type": "status_update",
                "request_id": request_id,
                "progress": progress_data.get("progress", 0),
                "stage": progress_data.get("current_stage", ""),
                "status": progress_data.get("status", "unknown"),
                "timestamp": progress_data.get("updated_at")
            }
        
        # Fallback to agent state
        agent_state = await redis_service.get_cached_agent_state(request_id)
        
        if agent_state:
            return {
                "type": "status_update",
                "request_id": request_id,
                "progress": agent_state.get("progress", 0),
                "stage": agent_state.get("current_stage", ""),
                "status": agent_state.get("status", "unknown"),
                "completed_stages": agent_state.get("completed_stages", []),
                "errors": agent_state.get("errors", []),
                "warnings": agent_state.get("warnings", [])
            }
        
        return {
            "type": "status_update",
            "request_id": request_id,
            "progress": 0,
            "stage": "unknown",
            "status": "not_found"
        }
    
    except Exception as e:
        logger.error(f"Error getting analysis status: {e}")
        return {
            "type": "error",
            "message": "Failed to get analysis status"
        }


@router.websocket("/system")
async def websocket_system_updates(websocket: WebSocket):
    """
    WebSocket endpoint for system-wide updates
    
    Provides real-time updates about:
    - System health
    - Active analyses count
    - Resource usage
    """
    await websocket.accept()
    
    try:
        while True:
            # Send system status update
            system_status = {
                "type": "system_status",
                "active_connections": sum(
                    len(connections) for connections in manager.active_connections.values()
                ),
                "active_analyses": len(manager.active_connections),
                "timestamp": asyncio.get_event_loop().time()
            }
            
            await websocket.send_text(json.dumps(system_status))
            
            # Wait before next update
            await asyncio.sleep(30)  # Update every 30 seconds
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"System WebSocket error: {e}")


# Utility function to send updates from other parts of the application
async def broadcast_analysis_update(request_id: str, update_data: dict):
    """
    Utility function to broadcast updates to connected clients
    
    This can be called from other parts of the application to send
    real-time updates to connected WebSocket clients.
    """
    await manager.broadcast_to_analysis(update_data, request_id)