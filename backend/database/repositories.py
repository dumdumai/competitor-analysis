from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from loguru import logger

from models.analysis import AnalysisResult, AnalysisRequest
from models.reports import Report
from models.agent_state import AgentState
from .connection import get_database


class AnalysisRepository:
    """Repository for analysis-related database operations"""
    
    def __init__(self):
        self.db: Optional[AsyncIOMotorDatabase] = None
    
    async def _get_db(self):
        if self.db is None:
            self.db = await get_database()
        return self.db
    
    async def create_analysis(self, request: AnalysisRequest) -> str:
        """Create a new analysis record"""
        try:
            db = await self._get_db()
            
            # Generate unique request_id
            request_id = str(ObjectId())
            
            analysis_result = AnalysisResult(
                request_id=request_id,
                client_company=request.client_company,
                industry=request.industry,
                target_market=request.target_market,
                business_model=request.business_model,
                specific_requirements=request.specific_requirements,
                max_competitors=request.max_competitors,
                status="pending",
                created_at=datetime.utcnow()
            )
            
            # Insert the analysis
            result = await db.analyses.insert_one(analysis_result.dict(exclude={"id"}))
            
            logger.info(f"Created analysis with ID: {result.inserted_id}")
            return request_id
            
        except Exception as e:
            logger.error(f"Error creating analysis: {e}")
            raise
    
    async def get_analysis(self, request_id: str) -> Optional[AnalysisResult]:
        """Get analysis by request_id"""
        try:
            db = await self._get_db()
            doc = await db.analyses.find_one({"request_id": request_id})
            
            if doc:
                doc["_id"] = str(doc["_id"])
                return AnalysisResult(**doc)
            return None
            
        except Exception as e:
            logger.error(f"Error getting analysis {request_id}: {e}")
            return None
    
    async def update_analysis(self, request_id: str, updates: Dict[str, Any]) -> bool:
        """Update analysis with new data"""
        try:
            db = await self._get_db()
            
            # Add updated_at timestamp
            updates["updated_at"] = datetime.utcnow()
            
            result = await db.analyses.update_one(
                {"request_id": request_id},
                {"$set": updates}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating analysis {request_id}: {e}")
            return False
    
    async def save_agent_state(self, state: AgentState) -> bool:
        """Save or update agent state"""
        try:
            db = await self._get_db()
            
            result = await db.agent_states.update_one(
                {"request_id": state.request_id},
                {"$set": state.dict()},
                upsert=True
            )
            
            return result.acknowledged
            
        except Exception as e:
            logger.error(f"Error saving agent state for {state.request_id}: {e}")
            return False
    
    async def get_agent_state(self, request_id: str) -> Optional[AgentState]:
        """Get agent state by request_id"""
        try:
            db = await self._get_db()
            doc = await db.agent_states.find_one({"request_id": request_id})
            
            if doc:
                return AgentState(**doc)
            return None
            
        except Exception as e:
            logger.error(f"Error getting agent state {request_id}: {e}")
            return None
    
    async def list_analyses(self, 
                           client_company: Optional[str] = None,
                           status: Optional[str] = None,
                           limit: int = 50) -> List[AnalysisResult]:
        """List analyses with optional filters"""
        try:
            db = await self._get_db()
            
            query = {}
            if client_company:
                query["client_company"] = {"$regex": client_company, "$options": "i"}
            if status:
                query["status"] = status
            
            cursor = db.analyses.find(query).sort("created_at", -1).limit(limit)
            analyses = []
            
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                analyses.append(AnalysisResult(**doc))
            
            return analyses
            
        except Exception as e:
            logger.error(f"Error listing analyses: {e}")
            return []


class ReportRepository:
    """Repository for report-related database operations"""
    
    def __init__(self):
        self.db: Optional[AsyncIOMotorDatabase] = None
    
    async def _get_db(self):
        if self.db is None:
            self.db = await get_database()
        return self.db
    
    async def create_report(self, report: Report) -> str:
        """Create a new report"""
        try:
            db = await self._get_db()
            
            result = await db.reports.insert_one(report.dict(exclude={"id"}))
            
            logger.info(f"Created report with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error creating report: {e}")
            raise
    
    async def get_report(self, report_id: str) -> Optional[Report]:
        """Get report by ID"""
        try:
            db = await self._get_db()
            doc = await db.reports.find_one({"_id": ObjectId(report_id)})
            
            if doc:
                doc["_id"] = str(doc["_id"])
                return Report(**doc)
            return None
            
        except Exception as e:
            logger.error(f"Error getting report {report_id}: {e}")
            return None
    
    async def get_report_by_analysis(self, analysis_id: str) -> Optional[Report]:
        """Get report by analysis ID"""
        try:
            db = await self._get_db()
            doc = await db.reports.find_one({"analysis_id": analysis_id})
            
            if doc:
                doc["_id"] = str(doc["_id"])
                return Report(**doc)
            return None
            
        except Exception as e:
            logger.error(f"Error getting report for analysis {analysis_id}: {e}")
            return None
    
    async def list_reports(self, 
                          client_company: Optional[str] = None,
                          limit: int = 50) -> List[Report]:
        """List reports with optional filters"""
        try:
            db = await self._get_db()
            
            query = {}
            if client_company:
                query["client_company"] = {"$regex": client_company, "$options": "i"}
            
            cursor = db.reports.find(query).sort("created_at", -1).limit(limit)
            reports = []
            
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                reports.append(Report(**doc))
            
            return reports
            
        except Exception as e:
            logger.error(f"Error listing reports: {e}")
            return []