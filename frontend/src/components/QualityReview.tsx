import React, { useState, useEffect } from 'react';
import { analysisAPI } from '../services/api';
import { 
  AlertTriangle, 
  CheckCircle, 
  RotateCcw, 
  Settings, 
  StopCircle,
  AlertCircle,
  Info,
  RefreshCw,
  Loader,
  X
} from 'lucide-react';
import { 
  Radio, 
  RadioGroup, 
  FormControlLabel, 
  FormControl, 
  FormLabel, 
  Button, 
  Card, 
  CardContent,
  Typography,
  Box,
  TextField,
  Container,
  Chip,
  Alert,
  List,
  Paper
} from '@mui/material';

interface QualityIssue {
  issue_type: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  description: string;
  affected_competitors: string[];
  suggested_action: string;
  retry_agent: 'search' | 'analysis' | null;
  additional_params: Record<string, any>;
}

interface QualityReviewData {
  request_id: string;
  quality_issues: QualityIssue[];
  current_analysis: {
    competitors_found: number;
    quality_scores: Record<string, number>;
    average_quality: number;
    analysis_completed: boolean;
  };
  available_actions: Array<{
    id: string;
    label: string;
    description: string;
  }>;
}

interface HumanReviewDecision {
  decision: string;
  feedback?: string;
  modified_params?: Record<string, any>;
  selected_issues?: string[];
}

interface QualityReviewProps {
  requestId: string;
  onDecisionSubmitted: (decision: HumanReviewDecision) => void;
  onGoBack?: () => void;
}

const QualityReview: React.FC<QualityReviewProps> = ({ requestId, onDecisionSubmitted, onGoBack }) => {
  const [reviewData, setReviewData] = useState<QualityReviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [selectedAction, setSelectedAction] = useState<string>('');
  const [feedback, setFeedback] = useState<string>('');
  const [modifiedParams, setModifiedParams] = useState<Record<string, any>>({});
  const [selectedIssues, setSelectedIssues] = useState<string[]>([]);
  const [showParamsModal, setShowParamsModal] = useState(false);

  useEffect(() => {
    fetchReviewData();
  }, [requestId]); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchReviewData = async () => {
    try {
      setLoading(true);
      const response = await analysisAPI.getQualityReview(requestId);
      setReviewData(response.data);
    } catch (error) {
      console.error('Error fetching quality review:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitDecision = async (event?: React.MouseEvent) => {
    // Prevent any default behavior
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }
    
    console.log('🔥 handleSubmitDecision called with selectedAction:', selectedAction);
    
    if (!selectedAction) {
      console.log('❌ No action selected, returning early');
      return;
    }

    const decision: HumanReviewDecision = {
      decision: selectedAction,
      feedback: feedback || undefined,
      modified_params: Object.keys(modifiedParams).length > 0 ? modifiedParams : undefined,
      selected_issues: selectedIssues.length > 0 ? selectedIssues : undefined,
    };

    try {
      setSubmitting(true);
      // Use API service but handle response similar to raw fetch for compatibility
      let response;
      try {
        const apiResponse = await analysisAPI.submitQualityDecision(requestId, decision);
        // Create a fetch-like response object for compatibility with existing error handling
        response = {
          ok: true,
          status: 200,
          statusText: 'OK',
          json: async () => apiResponse.data
        };
      } catch (apiError: any) {
        // Handle API service errors and convert to fetch-like response
        response = {
          ok: false,
          status: apiError.response?.status || 500,
          statusText: apiError.response?.statusText || 'Unknown Error',
          json: async () => apiError.response?.data || { detail: apiError.message }
        };
      }

      if (!response.ok) {
        console.log('❌ Response not OK:', response.status, response.statusText);
        
        try {
          const errorData = await response.json();
          console.log('📄 Error data:', errorData);
          
          // Handle specific backend bug where awaiting_human_review flag is not set
          if (response.status === 400 && errorData.detail?.includes('not currently awaiting human review')) {
            console.log('🐛 Detected backend bug - showing user-friendly message');
            
            // Show user-friendly error message with instructions
            const userMessage = `⚠️ Backend Issue Detected

The system has a temporary issue where the human review flag wasn't set properly. This is a known bug.

To proceed, you can:
1. Refresh the page and try again
2. Contact support with analysis ID: ${requestId}
3. Or restart the analysis from the beginning

The analysis data is safe and this issue is being addressed.`;
            
            console.log('🚨 Showing alert:', userMessage);
            alert(userMessage);
            console.log('✅ Alert should have been shown');
            return;
          }
        } catch (parseError) {
          console.log('❌ Failed to parse error response:', parseError);
          
          // If we can't parse the response but got a 400, it's likely the same bug
          if (response.status === 400) {
            console.log('🐛 Assuming backend bug due to 400 status');
            alert(`⚠️ Backend Issue Detected

There was an issue with the quality review submission. This appears to be a known backend bug.

Analysis ID: ${requestId}

Please refresh the page and try again, or contact support.`);
            return;
          }
        }
        
        throw new Error(`Failed to submit decision: ${response.status} ${response.statusText}`);
      }

      await response.json();
      onDecisionSubmitted(decision);
    } catch (error) {
      console.error('Error submitting decision:', error);
      
      // Show generic error if not the specific backend bug
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      if (!errorMessage.includes('not currently awaiting human review')) {
        alert(`Error submitting decision: ${errorMessage}

Please try again or contact support if the issue persists.`);
      }
    } finally {
      setSubmitting(false);
    }
  };


  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <AlertTriangle className="w-5 h-5 text-red-500" />;
      case 'high':
        return <AlertCircle className="w-5 h-5 text-orange-500" />;
      case 'medium':
        return <Info className="w-5 h-5 text-yellow-500" />;
      case 'low':
        return <CheckCircle className="w-5 h-5 text-blue-500" />;
      default:
        return <Info className="w-5 h-5 text-gray-500" />;
    }
  };

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'proceed': return <CheckCircle className="w-4 h-4" />;
      case 'retry_search': 
      case 'retry_analysis': return <RotateCcw className="w-4 h-4" />;
      case 'modify_params': return <Settings className="w-4 h-4" />;
      case 'abort': return <StopCircle className="w-4 h-4" />;
      default: return null;
    }
  };

  const getActionButtonText = (action: string) => {
    switch (action) {
      case 'proceed': return 'Proceed with Analysis';
      case 'retry_search': return 'Retry Search';
      case 'retry_analysis': return 'Retry Analysis';
      case 'modify_params': return 'Apply Changes & Retry';
      case 'abort': return 'Abort Analysis';
      default: return 'Submit Decision';
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', py: 12 }}>
          <Loader className="animate-spin mr-3" size={32} color="#1976d2" />
          <Typography variant="h6" color="text.secondary">
            Loading quality review...
          </Typography>
        </Box>
      </Container>
    );
  }

  // Check if we have no review data or empty quality issues
  if (!reviewData || !reviewData.quality_issues || reviewData.quality_issues.length === 0) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Card sx={{ borderRadius: 2, boxShadow: 3, maxWidth: 600, mx: 'auto' }}>
          <CardContent sx={{ p: { xs: 3, md: 4 } }}>
            <Box sx={{ textAlign: 'center' }}>
              {!reviewData ? 
                <AlertCircle size={48} color="#ff9800" style={{ marginBottom: 16 }} /> :
                <CheckCircle size={48} color="#4caf50" style={{ marginBottom: 16 }} />
              }
              <Typography variant="h5" component="h3" gutterBottom color="text.primary" fontWeight="600">
                {!reviewData ? 'Quality Review Data Not Found' : 'No Quality Issues Detected'}
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                {!reviewData ? 
                  'The system indicated that human review is required, but no quality review data was found. This may be due to:' :
                  'The quality check completed but found no issues requiring human review. This may indicate:'}
              </Typography>
              <Box sx={{ textAlign: 'left', mb: 3, ml: 4 }}>
                {!reviewData ? (
                  <>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      • The quality check process didn't complete properly
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      • The review data wasn't saved correctly
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      • The analysis was already approved by another user
                    </Typography>
                  </>
                ) : (
                  <>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      • All quality checks passed successfully
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      • The analysis data meets quality standards
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      • No manual intervention is needed
                    </Typography>
                  </>
                )}
              </Box>
              
              <Alert severity={reviewData ? "success" : "info"} sx={{ mb: 3, textAlign: 'left' }}>
                <Typography variant="body2">
                  <strong>{reviewData ? 'Good news!' : 'What you can do:'}</strong> {reviewData ? 
                    'The analysis passed all quality checks. You can proceed to view the results.' :
                    'You can go back to view the results as they are, or restart the analysis if you believe there\'s an issue.'}
                </Typography>
              </Alert>
              
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
                {onGoBack && (
                  <Button
                    variant="contained"
                    onClick={onGoBack}
                    sx={{ textTransform: 'none', fontWeight: 600 }}
                  >
                    View Results Anyway
                  </Button>
                )}
                <Button
                  variant="outlined"
                  onClick={() => window.location.reload()}
                  sx={{ textTransform: 'none', fontWeight: 600 }}
                >
                  Refresh Page
                </Button>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Container>
    );
  }

  const { quality_issues, current_analysis, available_actions } = reviewData;
  const criticalIssues = quality_issues.filter(issue => issue.severity === 'critical' || issue.severity === 'high');

  return (
    <Box sx={{ 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      py: { xs: 2, md: 4 },
      px: { xs: 2, md: 3 }
    }}>
      <Container maxWidth="xl">
        {/* Header */}
        <Box sx={{ mb: { xs: 3, md: 4 } }}>
          <Typography 
            variant="h4" 
            component="h2" 
            gutterBottom 
            fontWeight="bold"
            sx={{ color: 'white', textAlign: 'center', mb: 3 }}
          >
            Quality Review Required
          </Typography>
          
          <Card sx={{ borderRadius: 2, boxShadow: 3 }}>
            <Alert 
              severity="warning" 
              icon={<AlertTriangle size={20} />}
              sx={{ 
                borderRadius: 2,
                border: 'none',
                '& .MuiAlert-message': { width: '100%' }
              }}
            >
              <Typography variant="h6" component="h3" sx={{ mb: 1, fontWeight: 600 }}>
                Analysis Quality Check
              </Typography>
              <Typography variant="body2">
                The quality agent has identified {quality_issues.length} issues that require your review before proceeding.
                {criticalIssues.length > 0 && ` ${criticalIssues.length} of these are critical or high priority.`}
              </Typography>
            </Alert>
          </Card>
        </Box>

        {/* Analysis Summary */}
        <Box sx={{ mb: { xs: 3, md: 4 } }}>
          <Card sx={{ borderRadius: 2, boxShadow: 3 }}>
            <CardContent sx={{ p: { xs: 3, md: 4 } }}>
              <Typography variant="h5" component="h3" gutterBottom fontWeight="600" sx={{ mb: 3 }}>
                Analysis Summary
              </Typography>
              
              <Box sx={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(3, 1fr)', 
                gap: 3
              }}>
                <Box sx={{ 
                  p: { xs: 3, md: 4 }, 
                  textAlign: 'center', 
                  border: '1px solid #e0e0e0',
                  borderRadius: 2,
                  backgroundColor: '#f8f9fa'
                }}>
                  <Typography variant="h2" component="div" sx={{ color: '#1976d2', fontWeight: 700, mb: 1 }}>
                    {current_analysis.competitors_found}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" fontWeight="500">
                    Competitors Found
                  </Typography>
                </Box>
                
                <Box sx={{ 
                  p: { xs: 3, md: 4 }, 
                  textAlign: 'center', 
                  border: '1px solid #e0e0e0',
                  borderRadius: 2,
                  backgroundColor: '#f8f9fa'
                }}>
                  <Typography 
                    variant="h2" 
                    component="div" 
                    sx={{ 
                      color: current_analysis.average_quality >= 0.7 ? '#4caf50' : '#ff9800',
                      fontWeight: 700,
                      mb: 1
                    }}
                  >
                    {(current_analysis.average_quality * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary" fontWeight="500">
                    Average Quality Score
                  </Typography>
                </Box>
                
                <Box sx={{ 
                  p: { xs: 3, md: 4 }, 
                  textAlign: 'center', 
                  border: '1px solid #e0e0e0',
                  borderRadius: 2,
                  backgroundColor: '#f8f9fa'
                }}>
                  <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
                    {current_analysis.analysis_completed ? (
                      <CheckCircle size={40} color="#4caf50" />
                    ) : (
                      <Loader size={40} className="animate-spin" color="#2196f3" />
                    )}
                  </Box>
                  <Typography variant="body2" color="text.secondary" fontWeight="500">
                    {current_analysis.analysis_completed ? 'Completed' : 'In Progress'}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', lg: 'row' }, gap: { xs: 3, md: 4 } }}>
          {/* Quality Issues */}
          <Box sx={{ flex: 1, order: { xs: 2, lg: 1 } }}>
            <Card sx={{ borderRadius: 2, boxShadow: 3 }}>
              <CardContent sx={{ p: { xs: 3, md: 4 } }}>
                <Typography variant="h5" component="h3" gutterBottom fontWeight="600" sx={{ mb: 3 }}>
                  Quality Issues ({quality_issues.length})
                </Typography>
                
                <Box sx={{ mt: 2 }}>
                  {quality_issues.map((issue: QualityIssue, index: number) => (
                    <Box key={index} sx={{ mb: 3 }}>
                      <Card 
                        sx={{ 
                          border: '2px solid',
                          borderColor: issue.severity === 'critical' ? '#f44336' : 
                                      issue.severity === 'high' ? '#ff9800' : 
                                      issue.severity === 'medium' ? '#2196f3' : '#4caf50',
                          borderRadius: 2,
                          backgroundColor: '#fafafa'
                        }}
                      >
                        <CardContent sx={{ p: { xs: 2, md: 3 } }}>
                          <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, alignItems: 'flex-start', gap: 2 }}>
                            <Box sx={{ mt: 0.5 }}>
                              {getSeverityIcon(issue.severity)}
                            </Box>
                            
                            <Box sx={{ flexGrow: 1 }}>
                              <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, gap: { xs: 1, sm: 0 }, mb: 2 }}>
                                <Typography variant="h6" component="h4" sx={{ textTransform: 'capitalize' }}>
                                  {issue.issue_type.replace(/_/g, ' ')}
                                </Typography>
                                <Chip 
                                  label={issue.severity}
                                  size="small"
                                  color={
                                    issue.severity === 'critical' ? 'error' : 
                                    issue.severity === 'high' ? 'warning' : 
                                    issue.severity === 'medium' ? 'info' : 'success'
                                  }
                                  sx={{ textTransform: 'capitalize' }}
                                />
                              </Box>
                              
                              <Typography variant="body1" sx={{ mb: 2, color: 'text.secondary' }}>
                                {issue.description}
                              </Typography>
                              
                              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                                <Typography variant="body2">
                                  <strong>Suggested Action:</strong> {issue.suggested_action}
                                </Typography>
                                
                                {issue.affected_competitors.length > 0 && (
                                  <Typography variant="body2">
                                    <strong>Affected Competitors:</strong> {issue.affected_competitors.join(', ')}
                                  </Typography>
                                )}
                                
                                {issue.retry_agent && (
                                  <Box sx={{ mt: 1 }}>
                                    <Typography variant="body2" component="span">
                                      <strong>Recommended Retry:</strong>{' '}
                                    </Typography>
                                    <Chip 
                                      label={`${issue.retry_agent} agent`}
                                      size="small"
                                      variant="outlined"
                                      color="primary"
                                    />
                                  </Box>
                                )}
                              </Box>
                              
                              <FormControlLabel
                                control={
                                  <Radio
                                    checked={selectedIssues.includes(issue.issue_type)}
                                    onChange={(e) => {
                                      if (e.target.checked) {
                                        setSelectedIssues([...selectedIssues, issue.issue_type]);
                                      } else {
                                        setSelectedIssues(selectedIssues.filter(id => id !== issue.issue_type));
                                      }
                                    }}
                                    color="primary"
                                  />
                                }
                                label="Address this issue"
                                sx={{ mt: 2 }}
                              />
                            </Box>
                          </Box>
                        </CardContent>
                      </Card>
                  </Box>
                ))}
                </Box>
              </CardContent>
            </Card>
          </Box>

        {/* Action Selection */}
        <Box sx={{ width: { xs: '100%', lg: '33%' }, order: { xs: 1, lg: 2 } }}>
          <Card sx={{ position: { lg: 'sticky' }, top: 20, height: 'fit-content' }}>
            <CardContent>
          <Typography variant="h6" component="h3" gutterBottom>
            Choose Your Action
          </Typography>
          
          <FormControl component="fieldset" fullWidth sx={{ mt: 2 }}>
            <FormLabel component="legend" required>
              Select an action to proceed with the analysis
            </FormLabel>
            <RadioGroup
              value={selectedAction}
              onChange={(e) => setSelectedAction(e.target.value)}
              sx={{ mt: 2 }}
            >
              {available_actions.map(action => (
                <FormControlLabel
                  key={action.id}
                  value={action.id}
                  control={<Radio />}
                  label={
                    <Box>
                      <Typography variant="subtitle1" component="div">
                        {action.label}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {action.description}
                      </Typography>
                    </Box>
                  }
                  sx={{ 
                    alignItems: 'flex-start',
                    mb: 2,
                    ml: 0,
                    border: selectedAction === action.id ? '2px solid #1976d2' : '1px solid #e0e0e0',
                    borderRadius: 2,
                    p: 2,
                    '&:hover': {
                      backgroundColor: 'rgba(25, 118, 210, 0.04)'
                    }
                  }}
                />
              ))}
            </RadioGroup>
          </FormControl>

          <TextField
            fullWidth
            multiline
            rows={3}
            label="Feedback (Optional)"
            placeholder="Provide any additional feedback or instructions..."
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            sx={{ mt: 2 }}
          />

          {selectedAction === 'modify_params' && (
            <Button
              variant="outlined"
              startIcon={<Settings size={16} />}
              onClick={() => setShowParamsModal(true)}
              sx={{ mt: 2 }}
            >
              Modify Analysis Parameters
            </Button>
          )}

          {/* Action Buttons */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
            <Button
              variant="outlined"
              startIcon={<RefreshCw size={16} />}
              onClick={fetchReviewData}
            >
              Refresh Data
            </Button>
            
            <Button
              variant="contained"
              startIcon={submitting ? <Loader size={16} className="animate-spin" /> : getActionIcon(selectedAction)}
              onClick={handleSubmitDecision}
              disabled={!selectedAction || submitting}
              size="large"
            >
              {submitting ? 'Submitting...' : getActionButtonText(selectedAction)}
            </Button>
          </Box>
            </CardContent>
          </Card>
        </Box>
      </Box>

        {/* Parameters Modification Modal */}
        {showParamsModal && (
          <Box sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1300
          }}>
            <Card sx={{ width: 400, maxWidth: '90vw', borderRadius: 2 }}>
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                  <Typography variant="h6" component="h3" fontWeight="600">
                    Modify Analysis Parameters
                  </Typography>
                  <Button
                    onClick={() => setShowParamsModal(false)}
                    sx={{ minWidth: 'auto', p: 0.5, color: 'text.secondary' }}
                  >
                    <X size={20} />
                  </Button>
                </Box>
                
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                  <TextField
                    type="number"
                    label="Max Competitors"
                    placeholder="e.g., 10"
                    value={modifiedParams.max_competitors || ''}
                    onChange={(e) => setModifiedParams({
                      ...modifiedParams,
                      max_competitors: parseInt(e.target.value) || undefined
                    })}
                    fullWidth
                    variant="outlined"
                  />
                  
                  <TextField
                    label="Industry Focus"
                    placeholder="e.g., SaaS, E-commerce"
                    value={modifiedParams.industry || ''}
                    onChange={(e) => setModifiedParams({
                      ...modifiedParams,
                      industry: e.target.value
                    })}
                    fullWidth
                    variant="outlined"
                  />
                  
                  <TextField
                    label="Target Market"
                    placeholder="e.g., B2B, Enterprise"
                    value={modifiedParams.target_market || ''}
                    onChange={(e) => setModifiedParams({
                      ...modifiedParams,
                      target_market: e.target.value
                    })}
                    fullWidth
                    variant="outlined"
                  />
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 4 }}>
                  <Button
                    onClick={() => setShowParamsModal(false)}
                    variant="outlined"
                    sx={{ textTransform: 'none' }}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={() => setShowParamsModal(false)}
                    variant="contained"
                    sx={{ textTransform: 'none' }}
                  >
                    Apply Changes
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Box>
        )}
      </Container>
    </Box>
  );
};

export default QualityReview;