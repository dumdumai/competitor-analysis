import React, { useEffect, useState } from 'react';
import { 
  Search, 
  Brain, 
  CheckCircle, 
  UserCheck, 
  FileText,
  AlertTriangle,
  Clock,
  Loader,
  ChevronRight,
  Shield
} from 'lucide-react';
import {
  Box,
  Typography,
  Button,
  Paper,
  alpha
} from '@mui/material';
import { analysisAPI } from '../services/api';

interface WorkflowNode {
  id: string;
  name: string;
  status: 'pending' | 'active' | 'completed' | 'error' | 'waiting';
  icon: React.ElementType;
  description?: string;
  progress?: number;
  color: string;
}

interface WorkflowVisualizationProps {
  currentStage?: string;
  status?: string;
  requestId: string;
  onRefresh?: () => void;
  showTitle?: boolean;
  onHumanReviewClick?: () => void;
}

const WorkflowVisualization: React.FC<WorkflowVisualizationProps> = ({ 
  currentStage = '',
  status = 'pending',
  requestId,
  onRefresh,
  showTitle = true,
  onHumanReviewClick
}) => {
  const [nodes, setNodes] = useState<WorkflowNode[]>([]);
  const [currentProgress, setCurrentProgress] = useState<string>('');
  // Disable auto-refresh by default when in human_review stage
  const [autoRefresh, setAutoRefresh] = useState(currentStage !== 'human_review');
  const [lastUpdated, setLastUpdated] = useState<string>('');
  const [completedStages, setCompletedStages] = useState<string[]>([]);

  // Define the workflow nodes
  const workflowNodes: WorkflowNode[] = [
    {
      id: 'search',
      name: 'Search Agent',
      status: 'pending',
      icon: Search,
      color: '#2196f3',
      description: 'Discovering competitors and collecting data'
    },
    {
      id: 'analysis',
      name: 'Analysis Agent',
      status: 'pending',
      icon: Brain,
      color: '#ff9800',
      description: 'Analyzing market and competitive positioning'
    },
    {
      id: 'quality',
      name: 'Quality Agent',
      status: 'pending',
      icon: Shield,
      color: '#4caf50',
      description: 'Validating data quality and completeness'
    },
    {
      id: 'human_review',
      name: 'Human Review',
      status: 'pending',
      icon: UserCheck,
      color: '#9c27b0',
      description: 'Awaiting human decision on quality issues'
    },
    {
      id: 'report',
      name: 'Report Generation',
      status: 'pending',
      icon: FileText,
      color: '#f44336',
      description: 'Generating final analysis report'
    }
  ];

  // Update node statuses based on current stage
  useEffect(() => {
    const updateNodeStatuses = () => {
      const updatedNodes = [...workflowNodes];
      
      // Reset all nodes
      updatedNodes.forEach(node => {
        node.status = 'pending';
      });

      // Update based on current stage and status
      if (status === 'completed') {
        // If completed, mark all nodes as completed
        updatedNodes[0].status = 'completed'; // search
        updatedNodes[1].status = 'completed'; // analysis
        updatedNodes[2].status = 'completed'; // quality
        updatedNodes[3].status = 'completed'; // human_review (completed via skip or approval)
        updatedNodes[4].status = 'completed'; // report
      } else if (status === 'failed') {
        // Handle failed analyses - mark stages up to where it failed
        const failedStageIndex = workflowNodes.findIndex(n => n.id === currentStage);
        if (failedStageIndex >= 0) {
          for (let i = 0; i < failedStageIndex; i++) {
            updatedNodes[i].status = 'completed';
          }
          updatedNodes[failedStageIndex].status = 'error';
        } else {
          // Default failed state
          updatedNodes[0].status = 'error';
        }
      } else if (status === 'in_progress' || status === 'pending') {
        // Handle in-progress states
        switch (currentStage) {
          case 'search':
          case 'searching':
            updatedNodes[0].status = 'active';
            break;
          case 'analysis':
          case 'analyzing':
            updatedNodes[0].status = 'completed';
            updatedNodes[1].status = 'active';
            break;
          case 'quality':
          case 'quality_check':
            updatedNodes[0].status = 'completed';
            updatedNodes[1].status = 'completed';
            updatedNodes[2].status = 'active';
            break;
          case 'human_review':
            updatedNodes[0].status = 'completed';
            updatedNodes[1].status = 'completed';
            updatedNodes[2].status = 'completed';
            updatedNodes[3].status = 'active';
            break;
          case 'report':
          case 'reporting':
            updatedNodes[0].status = 'completed';
            updatedNodes[1].status = 'completed';
            updatedNodes[2].status = 'completed';
            updatedNodes[3].status = 'completed';
            updatedNodes[4].status = 'active';
            break;
          default:
            if (!currentStage && status === 'pending') {
              // Starting state
              updatedNodes[0].status = 'active';
            }
        }
      }

      setNodes(updatedNodes);
    };

    updateNodeStatuses();
  }, [currentStage, status]);

  // Fetch initial completed stages on mount
  useEffect(() => {
    const fetchInitialStatus = async () => {
      try {
        const response = await analysisAPI.getAnalysisStatus(requestId);
        const data = response.data;
        if (data.completed_stages) {
          setCompletedStages(data.completed_stages);
        }
      } catch (error) {
        console.error('Error fetching initial status:', error);
      }
    };
    fetchInitialStatus();
  }, [requestId]);

  // Fetch progress updates - only refresh workflow data, not entire page
  useEffect(() => {
    // Don't auto-refresh when in human_review stage to prevent constant reloading
    if (!autoRefresh || status === 'completed' || status === 'failed' || currentStage === 'human_review') return;

    const fetchProgress = async () => {
      try {
        // Fetch just the analysis status to update workflow
        const response = await analysisAPI.getAnalysisStatus(requestId);
        const data = response.data;
        setCurrentProgress(data.message || data.current_stage || '');
        setLastUpdated(new Date().toLocaleTimeString());
        // Update completed stages from backend
        if (data.completed_stages) {
          setCompletedStages(data.completed_stages);
        }
          
        // Update the workflow nodes based on new status
        if (data.status !== status || data.current_stage !== currentStage) {
          // Call onRefresh only if there's a significant change
          if (onRefresh && (data.status === 'completed' || data.status === 'failed')) {
            onRefresh();
          }
        }
      } catch (error) {
        console.error('Error fetching progress:', error);
      }
    };

    const interval = setInterval(fetchProgress, 3000); // Poll every 3 seconds
    return () => clearInterval(interval);
  }, [requestId, autoRefresh, status, currentStage, onRefresh]);

  // Local refresh function that doesn't trigger full page refresh
  const handleLocalRefresh = async () => {
    try {
      const response = await analysisAPI.getAnalysisStatus(requestId);
      const data = response.data;
      setCurrentProgress(data.message || data.current_stage || '');
      setLastUpdated(new Date().toLocaleTimeString());
      
      // Update completed stages
      if (data.completed_stages) {
        setCompletedStages(data.completed_stages);
      }
      
      // Only trigger full refresh if analysis is completed or failed
      if (onRefresh && (data.status === 'completed' || data.status === 'failed')) {
        onRefresh();
      }
    } catch (error) {
      console.error('Error refreshing workflow:', error);
    }
  };

  const getNodeColor = (nodeStatus: string) => {
    switch (nodeStatus) {
      case 'completed':
        return 'text-green-600 bg-green-50 border-green-300';
      case 'active':
        return 'text-blue-600 bg-blue-50 border-blue-300 animate-pulse';
      case 'waiting':
        return 'text-yellow-600 bg-yellow-50 border-yellow-300';
      case 'error':
        return 'text-red-600 bg-red-50 border-red-300';
      default:
        return 'text-gray-400 bg-gray-50 border-gray-200';
    }
  };

  const getStatusIcon = (nodeStatus: string) => {
    switch (nodeStatus) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'active':
        return <Loader className="w-4 h-4 text-blue-600 animate-spin" />;
      case 'waiting':
        return <Clock className="w-4 h-4 text-yellow-600" />;
      case 'error':
        return <AlertTriangle className="w-4 h-4 text-red-600" />;
      default:
        return null;
    }
  };

  return (
    <Box sx={{ backgroundColor: 'white', borderRadius: 2, boxShadow: 2, p: 4 }}>
      {showTitle && (
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
          <Typography variant="h5" component="h3" fontWeight="600" color="text.primary">
            Analysis Workflow
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {(status === 'in_progress' || status === 'pending') && (
              <Button
                onClick={() => setAutoRefresh(!autoRefresh)}
                variant={autoRefresh ? 'contained' : 'outlined'}
                size="small"
                color={autoRefresh ? 'success' : 'inherit'}
                sx={{ textTransform: 'none', fontSize: '0.75rem' }}
              >
                {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
              </Button>
            )}
            {(status === 'in_progress' || status === 'pending') && (
              <Button
                onClick={handleLocalRefresh}
                variant="outlined"
                size="small"
                sx={{ textTransform: 'none', fontSize: '0.75rem' }}
              >
                Refresh Workflow
              </Button>
            )}
          </Box>
        </Box>
      )}

      {/* Clean Linear Workflow - Matching Screenshot Style */}
      <Box sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        backgroundColor: '#f8f9fa',
        borderRadius: 2,
        p: 3,
        mb: 3,
        overflowX: 'auto'
      }}>
        {nodes.map((node, index) => {
          const Icon = node.icon;
          const isCompleted = node.status === 'completed';
          const isActive = node.status === 'active';
          const isError = node.status === 'error';
          
          const isHumanReview = node.id === 'human_review';
          const isClickable = isHumanReview && isActive && onHumanReviewClick;
          
          return (
            <React.Fragment key={node.id}>
              <Box sx={{ 
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                minWidth: '120px',
                position: 'relative',
                cursor: isClickable ? 'pointer' : 'default',
                backgroundColor: isClickable ? alpha('#ed6c02', 0.1) : 'transparent',
                borderRadius: isClickable ? 2 : 0,
                p: isClickable ? 2 : 0,
                '&:hover': isClickable ? {
                  transform: 'scale(1.05)',
                  transition: 'transform 0.2s ease',
                  backgroundColor: alpha('#ed6c02', 0.2),
                  boxShadow: `0 4px 20px ${alpha('#ed6c02', 0.3)}`
                } : {}
              }}
              onClick={isClickable ? onHumanReviewClick : undefined}
              >
                {/* Icon Circle */}
                <Box sx={{
                  width: 56,
                  height: 56,
                  borderRadius: '50%',
                  backgroundColor: isCompleted ? '#4caf50' : isError ? '#f44336' : isActive ? node.color : '#e0e0e0',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  mb: 1.5,
                  boxShadow: isActive ? `0 0 20px ${alpha(node.color, 0.4)}` : 'none',
                  transition: 'all 0.3s ease',
                  border: isClickable ? '3px solid' : 'none',
                  borderColor: isClickable ? node.color : 'transparent',
                  animation: isClickable ? 'pulse 2s infinite' : 'none',
                  '@keyframes pulse': {
                    '0%': {
                      boxShadow: `0 0 0 0 ${alpha(node.color, 0.4)}`,
                    },
                    '70%': {
                      boxShadow: `0 0 0 10px ${alpha(node.color, 0)}`,
                    },
                    '100%': {
                      boxShadow: `0 0 0 0 ${alpha(node.color, 0)}`,
                    },
                  }
                }}>
                  {isActive ? (
                    <Loader size={24} color="white" className="animate-spin" />
                  ) : isCompleted ? (
                    <CheckCircle size={24} color="white" />
                  ) : isError ? (
                    <AlertTriangle size={24} color="white" />
                  ) : (
                    <Icon size={24} color={isCompleted || isActive || isError ? "white" : "#9e9e9e"} />
                  )}
                </Box>
                
                {/* Agent Name */}
                <Typography 
                  variant="body2" 
                  fontWeight={isClickable ? "700" : "500"}
                  color={isActive ? node.color : isCompleted ? '#4caf50' : isError ? '#f44336' : 'text.secondary'}
                  sx={{ textAlign: 'center', lineHeight: 1.2 }}
                >
                  {node.name}
                </Typography>
                
                {/* Description for active state */}
                {isActive && (
                  <Typography 
                    variant="caption" 
                    color={isClickable ? "#ed6c02" : "text.secondary"}
                    fontWeight={isClickable ? "600" : "400"}
                    sx={{ 
                      textAlign: 'center', 
                      mt: 0.5, 
                      maxWidth: '100px',
                      fontSize: isClickable ? '0.8rem' : '0.75rem'
                    }}
                  >
                    {isClickable ? '👆 Click to Review' : node.description}
                  </Typography>
                )}
              </Box>
              
              {/* Arrow between nodes */}
              {index < nodes.length - 1 && (
                <ChevronRight 
                  size={20} 
                  color={nodes[index].status === 'completed' ? '#4caf50' : '#e0e0e0'}
                  style={{ 
                    margin: '0 8px',
                    transition: 'color 0.3s ease'
                  }}
                />
              )}
            </React.Fragment>
          );
        })}
      </Box>

      {/* Status Messages */}
      {status === 'completed' && (
        <Paper sx={{
          p: 2,
          backgroundColor: '#e8f5e8',
          border: '1px solid #4caf50',
          borderRadius: 2,
          mb: 3
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CheckCircle size={20} color="#4caf50" />
            <Typography variant="body2" color="#4caf50" fontWeight="500">
              Analysis completed successfully - All workflow stages executed
            </Typography>
          </Box>
        </Paper>
      )}

      {currentProgress && status !== 'completed' && (
        <Paper sx={{
          p: 2,
          backgroundColor: '#e3f2fd',
          border: '1px solid #2196f3',
          borderRadius: 2,
          mb: 3
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Loader size={16} color="#2196f3" className="animate-spin" />
              <Typography variant="body2" color="#2196f3">
                {currentProgress}
              </Typography>
            </Box>
            {lastUpdated && (
              <Typography variant="caption" color="text.secondary">
                Last updated: {lastUpdated}
              </Typography>
            )}
          </Box>
        </Paper>
      )}

      {/* Progress Summary */}
      <Box sx={{ 
        display: 'grid', 
        gridTemplateColumns: { xs: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, 
        gap: 2,
        mb: 2
      }}>
        <Paper sx={{ p: 2, backgroundColor: '#f5f5f5', textAlign: 'center' }}>
          <Typography variant="caption" color="text.secondary" fontWeight="500">
            Status
          </Typography>
          <Typography variant="body2" fontWeight="600" sx={{ textTransform: 'capitalize' }}>
            {status}
          </Typography>
        </Paper>
        <Paper sx={{ p: 2, backgroundColor: '#f5f5f5', textAlign: 'center' }}>
          <Typography variant="caption" color="text.secondary" fontWeight="500">
            Current Stage
          </Typography>
          <Typography variant="body2" fontWeight="600" sx={{ textTransform: 'capitalize' }}>
            {currentStage || 'Initializing'}
          </Typography>
        </Paper>
        <Paper sx={{ p: 2, backgroundColor: '#f5f5f5', textAlign: 'center' }}>
          <Typography variant="caption" color="text.secondary" fontWeight="500">
            Progress
          </Typography>
          <Typography variant="body2" fontWeight="600">
            {completedStages.length} / 5
          </Typography>
        </Paper>
        <Paper sx={{ p: 2, backgroundColor: '#f5f5f5', textAlign: 'center' }}>
          <Typography variant="caption" color="text.secondary" fontWeight="500">
            Request ID
          </Typography>
          <Typography variant="caption" fontWeight="600" sx={{ fontFamily: 'monospace' }}>
            {requestId.substring(0, 8)}...
          </Typography>
        </Paper>
      </Box>
    </Box>
  );
};

export default WorkflowVisualization;