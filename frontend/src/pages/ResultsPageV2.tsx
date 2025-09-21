import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, AlertCircle, RefreshCw, Bug, X, Loader, AlertTriangle, Settings, RotateCcw } from 'lucide-react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  Alert,
  Chip,
  Paper,
  Modal,
  Divider,
  IconButton
} from '@mui/material';
import { analysisAPI } from '../services/api';
import QualityReview from '../components/QualityReview';
import WorkflowVisualization from '../components/WorkflowVisualization';

interface AnalysisResult {
  request_id: string;
  client_company: string;
  industry: string;
  target_market?: string;
  business_model?: string;
  specific_requirements?: string;
  max_competitors?: number;
  status: string;
  current_stage?: string;
  competitors: any[];
  market_analysis: any;
  threats_opportunities?: {
    opportunities?: string[];
    threats?: string[];
  };
  recommendations: string[];
  created_at: string;
  updated_at: string;
  // Product analysis fields
  comparison_type?: string;
  client_product?: string;
  product_category?: string;
  comparison_criteria?: string[];
}

const ResultsPageV2: React.FC = () => {
  const { requestId } = useParams<{ requestId: string }>();
  const navigate = useNavigate();
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [searchLogs, setSearchLogs] = useState<any[]>([]);
  const [debugModalSection, setDebugModalSection] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [forceShowReview, setForceShowReview] = useState(false);

  useEffect(() => {
    if (requestId) {
      loadAnalysisResult();
    }
  }, [requestId]);

  // Auto-refresh for in-progress analysis
  useEffect(() => {
    let refreshInterval: NodeJS.Timeout;
    
    if (analysisResult && (analysisResult.status === 'in_progress' || analysisResult.status === 'pending')) {
      // Refresh every 10 seconds for in-progress analysis
      refreshInterval = setInterval(() => {
        loadAnalysisResult();
      }, 10000);
    }
    
    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, [analysisResult?.status]);


  const loadAnalysisResult = async () => {
    if (!requestId) return;

    try {
      setLoading(true);
      setError(null);
      
      const response = await analysisAPI.getAnalysisResult(requestId);
      setAnalysisResult(response.data);
      
      // Also load search logs if analysis is completed
      if (response.data.status === 'completed') {
        loadSearchLogs();
      }
      
    } catch (err: any) {
      console.error('Error loading analysis result:', err);
      setError(err?.response?.data?.detail || 'Failed to load analysis result');
    } finally {
      setLoading(false);
    }
  };

  const loadSearchLogs = async () => {
    if (!requestId) return;

    try {
      const response = await analysisAPI.getSearchLogs(requestId);
      setSearchLogs(response.data.search_logs || []);
    } catch (err: any) {
      console.error('Failed to load search logs:', err);
      // Don't set error for search logs as they're supplementary
    }
  };

  const openSectionDebug = (sectionType: string) => {
    if (searchLogs.length === 0) {
      loadSearchLogs();
    }
    setDebugModalSection(sectionType);
  };

  const getSectionSearchLogs = (sectionType: string) => {
    switch (sectionType) {
      case 'competitors':
        return searchLogs.filter(log => 
          log.search_type === 'competitor_search' || 
          log.search_type === 'company_details'
        );
      case 'market':
        return searchLogs.filter(log => log.search_type === 'market_analysis');
      default:
        return searchLogs;
    }
  };

  const handleRestartAnalysis = () => {
    if (!analysisResult) return;
    
    // Create prefilled form data from current analysis
    const formData = {
      client_company: analysisResult.client_company || '',
      industry: analysisResult.industry || '',
      target_market: analysisResult.target_market || '',
      business_model: analysisResult.business_model || '',
      specific_requirements: analysisResult.specific_requirements || '',
      max_competitors: analysisResult.max_competitors || 5
    };
    
    // Navigate to analysis form with prefilled data
    navigate('/analysis', { 
      state: { 
        prefillData: formData,
        isRestart: true,
        originalRequestId: requestId,
        originalCompany: analysisResult.client_company
      } 
    });
  };

  if (loading) {
    return (
      <Box sx={{ 
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        py: { xs: 2, md: 4 },
        px: { xs: 2, md: 3 },
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <Card sx={{ borderRadius: 2, boxShadow: 3, maxWidth: 500, textAlign: 'center' }}>
          <CardContent sx={{ p: { xs: 3, md: 4 } }}>
            <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
              <Loader className="animate-spin" size={48} color="#1976d2" />
            </Box>
            <Typography variant="h5" component="h2" gutterBottom fontWeight="600">
              Loading Analysis
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              We're preparing your competitive analysis results...
            </Typography>
            <Box sx={{ textAlign: 'left', color: 'text.secondary' }}>
              <Typography variant="body2" sx={{ mb: 0.5 }}>• Gathering analysis data</Typography>
              <Typography variant="body2" sx={{ mb: 0.5 }}>• Processing competitor information</Typography>
              <Typography variant="body2">• Generating insights</Typography>
            </Box>
          </CardContent>
        </Card>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ 
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        py: { xs: 2, md: 4 },
        px: { xs: 2, md: 3 },
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <Card sx={{ borderRadius: 2, boxShadow: 3, maxWidth: 500, textAlign: 'center' }}>
          <CardContent sx={{ p: { xs: 3, md: 4 } }}>
            <AlertCircle size={48} color="#f44336" style={{ margin: '0 auto 16px' }} />
            <Typography variant="h5" component="h2" gutterBottom fontWeight="600">
              Error Loading Analysis
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              {error}
            </Typography>
            <Button 
              onClick={loadAnalysisResult} 
              variant="contained" 
              fullWidth
              sx={{ textTransform: 'none', fontWeight: 600 }}
            >
              Try Again
            </Button>
          </CardContent>
        </Card>
      </Box>
    );
  }

  if (!analysisResult) {
    return (
      <Box sx={{ 
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        py: { xs: 2, md: 4 },
        px: { xs: 2, md: 3 },
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <Card sx={{ borderRadius: 2, boxShadow: 3, maxWidth: 500, textAlign: 'center' }}>
          <CardContent sx={{ p: { xs: 3, md: 4 } }}>
            <AlertCircle size={48} color="#9e9e9e" style={{ margin: '0 auto 16px' }} />
            <Typography variant="h5" component="h2" gutterBottom fontWeight="600">
              Analysis Not Found
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              The analysis you're looking for doesn't exist or may have been removed.
            </Typography>
            <Button 
              component={Link}
              to="/home"
              variant="outlined"
              sx={{ textTransform: 'none', fontWeight: 600 }}
            >
              Go Back to Dashboard
            </Button>
          </CardContent>
        </Card>
      </Box>
    );
  }

  // Handle decision submission callback
  const handleDecisionSubmitted = () => {
    // Refresh the analysis result after decision is submitted
    setForceShowReview(false);
    loadAnalysisResult();
  };

  // Debug logging for human review condition
  console.log('DEBUG - Analysis Result:', {
    status: analysisResult.status,
    current_stage: analysisResult.current_stage,
    condition1: analysisResult.status === 'in_progress',
    condition2: analysisResult.status === 'pending',
    condition3: analysisResult.current_stage !== 'human_review',
    willShowProgress: (analysisResult.status === 'in_progress' || analysisResult.status === 'pending') && analysisResult.current_stage !== 'human_review'
  });

  // Temporary debug banner - remove after fixing
  const showDebugBanner = false;

  // Special handling for in-progress analysis (but not human_review stage)
  if ((analysisResult.status === 'in_progress' || analysisResult.status === 'pending') && analysisResult.current_stage !== 'human_review') {
    return (
      <Box sx={{ 
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        py: { xs: 2, md: 4 },
        px: { xs: 2, md: 3 }
      }}>
        <Container maxWidth="xl">
          {/* Header */}
          <Card sx={{ borderRadius: 2, boxShadow: 3, mb: { xs: 3, md: 4 } }}>
            <CardContent sx={{ p: { xs: 3, md: 4 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <IconButton 
                  component={Link} 
                  to="/home" 
                  sx={{ color: 'text.secondary' }}
                >
                  <ArrowLeft size={20} />
                </IconButton>
                <Box>
                  <Typography variant="h4" component="h1" fontWeight="bold">
                    {analysisResult.client_company}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                    <Typography variant="body1" color="text.secondary">
                      {analysisResult.industry}
                    </Typography>
                    <Typography variant="body1" color="text.secondary">•</Typography>
                    <Chip 
                      label="Analysis in Progress" 
                      size="small" 
                      color="warning" 
                      sx={{ fontWeight: 500 }} 
                    />
                  </Box>
                </Box>
              </Box>
            </CardContent>
          </Card>

          {/* Progress Content */}
          {/* Workflow Visualization */}
          <Box sx={{ mb: { xs: 3, md: 4 } }}>
            <WorkflowVisualization 
              currentStage={analysisResult.current_stage}
              status={analysisResult.status}
              requestId={analysisResult.request_id}
              onHumanReviewClick={() => {
                if (analysisResult.current_stage === 'human_review') {
                  setForceShowReview(true);
                }
              }}
              onRefresh={loadAnalysisResult}
            />
          </Box>
          
          <Card sx={{ borderRadius: 2, boxShadow: 3, textAlign: 'center' }}>
            <CardContent sx={{ p: { xs: 4, md: 6 } }}>
              <Box sx={{ display: 'flex', justifyContent: 'center', mb: 4 }}>
                <Loader className="animate-spin" size={64} color="#ff9800" />
              </Box>
              <Typography variant="h4" component="h2" gutterBottom fontWeight="600">
                Analysis in Progress
              </Typography>
              <Typography variant="h6" color="text.secondary" sx={{ mb: 4 }}>
                We're analyzing the competitive landscape for <strong>{analysisResult.client_company}</strong> in the <strong>{analysisResult.industry}</strong> industry.
              </Typography>
              
              <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                This usually takes 2-5 minutes to complete.
              </Typography>
              <Button 
                onClick={loadAnalysisResult}
                variant="contained"
                color="warning"
                sx={{ textTransform: 'none', fontWeight: 600, px: 4 }}
              >
                Refresh Status
              </Button>
            </CardContent>
          </Card>
        </Container>
      </Box>
    );
  }

  return (
    <Box sx={{ 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      py: { xs: 2, md: 4 },
      px: { xs: 2, md: 3 }
    }}>
      <Container maxWidth="xl">
        {/* Debug Banner - Remove after fixing */}
        {showDebugBanner && (
          <Card sx={{ borderRadius: 2, boxShadow: 3, mb: 2, backgroundColor: '#ff9800', color: 'white' }}>
            <CardContent sx={{ p: 2 }}>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                DEBUG: Status={analysisResult.status}, Stage={analysisResult.current_stage}, 
                Condition={(analysisResult.status === 'in_progress' || analysisResult.status === 'pending') && analysisResult.current_stage !== 'human_review' ? 'SHOW_PROGRESS' : 'SHOW_RESULTS'}
              </Typography>
            </CardContent>
          </Card>
        )}
        
        {/* Header */}
        <Card sx={{ borderRadius: 2, boxShadow: 3, mb: { xs: 3, md: 4 } }}>
          <CardContent sx={{ p: { xs: 3, md: 4 } }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <IconButton 
                  component={Link} 
                  to="/home" 
                  sx={{ color: 'text.secondary' }}
                >
                  <ArrowLeft size={20} />
                </IconButton>
                <Box>
                  <Typography variant="h4" component="h1" fontWeight="bold">
                    {analysisResult.client_company}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                    <Typography variant="body1" color="text.secondary">
                      {analysisResult.industry}
                    </Typography>
                    <Typography variant="body1" color="text.secondary">•</Typography>
                    <Chip 
                      label={
                        analysisResult.status === 'completed' 
                          ? 'Completed'
                          : (analysisResult.current_stage === 'human_review' 
                              ? 'Review Required'
                              : analysisResult.status)
                      } 
                      size="small" 
                      color={
                        analysisResult.status === 'completed' 
                          ? 'success'
                          : (analysisResult.current_stage === 'human_review' 
                              ? 'warning'
                              : 'default')
                      } 
                      sx={{ fontWeight: 500, textTransform: 'capitalize' }} 
                    />
                  </Box>
                </Box>
              </Box>
              <Button
                onClick={handleRestartAnalysis}
                variant="outlined"
                startIcon={<RefreshCw size={16} />}
                sx={{ 
                  textTransform: 'none', 
                  fontWeight: 600,
                  color: 'text.secondary',
                  borderColor: 'text.secondary',
                  '&:hover': {
                    borderColor: 'primary.main',
                    color: 'primary.main'
                  }
                }}
              >
                Restart Analysis
              </Button>
            </Box>
          </CardContent>
        </Card>


        {/* Human Review Notice - Show when current_stage is 'human_review' and not completed */}
        {analysisResult.current_stage === 'human_review' && analysisResult.status !== 'completed' && !forceShowReview && (
          <Card sx={{ borderRadius: 2, boxShadow: 3, mb: { xs: 3, md: 4 }, border: '2px solid', borderColor: 'warning.main' }}>
            <CardContent sx={{ p: { xs: 3, md: 4 } }}>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2, mb: 2 }}>
                <AlertTriangle size={24} color="#ed6c02" />
                <Box sx={{ flex: 1 }}>
                  <Typography variant="h6" component="h3" fontWeight="600" sx={{ color: 'warning.main', mb: 1 }}>
                    {analysisResult.status === 'completed' ? 'Quality Review Available' : 'Human Review Required'}
                  </Typography>
                  <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                    {analysisResult.status === 'completed' 
                      ? 'This analysis has quality review data available for inspection. You can review the quality assessment and any issues found during analysis.'
                      : 'This analysis requires human review before completion. The AI workflow has completed initial processing but needs your review to finalize the results.'}
                  </Typography>
                  
                  {/* Show debug info if data is empty */}
                  {(analysisResult.competitors?.length === 0 && analysisResult.current_stage === 'human_review') && (
                    <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic', mb: 2 }}>
                      Note: The analysis appears to have completed processing but results data is pending review validation.
                    </Typography>
                  )}
                </Box>
              </Box>
              
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button 
                  variant="contained"
                  color="warning"
                  onClick={() => {
                    // Force show the human review interface
                    setForceShowReview(true);
                  }}
                  sx={{ fontWeight: 600, textTransform: 'none' }}
                  startIcon={<Settings size={16} />}
                >
                  {analysisResult.status === 'completed' ? 'View Quality Review' : 'Start Review Process'}
                </Button>
                {analysisResult.status === 'in_progress' && (
                  <Button 
                    variant="outlined"
                    color="warning"
                    onClick={async () => {
                      // Skip the review and mark as completed
                      if (window.confirm('Are you sure you want to skip the review and proceed with available results? This will mark the analysis as completed.')) {
                        try {
                          console.log('🚀 Skipping review and submitting proceed decision...');
                          
                          // Submit a proceed decision to complete the analysis
                          const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1'}/analysis/${requestId}/quality-review/decision`, {
                            method: 'POST',
                            headers: {
                              'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                              decision: 'proceed',
                              feedback: 'Review skipped by user',
                              selected_issues: [],
                              modified_params: {}
                            })
                          });
                          
                          if (response.ok) {
                            console.log('✅ Proceed decision submitted successfully');
                            // Reload the analysis result to get updated status
                            await loadAnalysisResult();
                          } else {
                            console.error('Failed to submit proceed decision:', await response.text());
                            alert('Failed to complete the analysis. Please try again.');
                          }
                        } catch (error) {
                          console.error('Error submitting proceed decision:', error);
                          alert('Failed to complete the analysis. Please try again.');
                        }
                      }
                    }}
                    sx={{ fontWeight: 600, textTransform: 'none' }}
                    startIcon={<RotateCcw size={16} />}
                  >
                    Skip Review & Complete
                  </Button>
                )}
                <Button 
                  variant="outlined"
                  onClick={loadAnalysisResult}
                  sx={{ fontWeight: 600, textTransform: 'none' }}
                  startIcon={<RefreshCw size={16} />}
                >
                  Refresh Status
                </Button>
              </Box>
            </CardContent>
          </Card>
        )}

        {/* Show Quality Review Component Inline when requested */}
        {forceShowReview && analysisResult.current_stage === 'human_review' && (
          <Card sx={{ borderRadius: 2, boxShadow: 3, mb: { xs: 3, md: 4 }, border: '2px solid', borderColor: 'warning.main' }}>
            <CardContent sx={{ p: 0 }}>
              <Box sx={{ 
                p: { xs: 2, md: 3 }, 
                borderBottom: '1px solid', 
                borderColor: 'divider',
                backgroundColor: 'warning.50'
              }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <AlertTriangle size={20} color="#ed6c02" />
                    <Typography variant="h6" fontWeight="600" color="warning.main">
                      Quality Review Panel
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      size="small"
                      onClick={handleRestartAnalysis}
                      variant="outlined"
                      startIcon={<RefreshCw size={16} />}
                      sx={{ 
                        color: 'text.secondary',
                        borderColor: 'text.secondary',
                        '&:hover': {
                          borderColor: 'primary.main',
                          color: 'primary.main'
                        }
                      }}
                    >
                      Restart
                    </Button>
                    <Button
                      size="small"
                      onClick={() => setForceShowReview(false)}
                      sx={{ color: 'text.secondary' }}
                      startIcon={<X size={16} />}
                    >
                      Close Review
                    </Button>
                  </Box>
                </Box>
              </Box>
              <Box sx={{ p: { xs: 2, md: 3 } }}>
                <QualityReview 
                  requestId={analysisResult.request_id} 
                  onDecisionSubmitted={handleDecisionSubmitted}
                  onGoBack={() => setForceShowReview(false)}
                />
              </Box>
            </CardContent>
          </Card>
        )}

        {/* Analysis Summary */}
        <Card sx={{ borderRadius: 2, boxShadow: 3, mb: { xs: 3, md: 4 } }}>
          <CardContent sx={{ p: { xs: 3, md: 4 } }}>
            <Typography variant="h4" component="h2" gutterBottom fontWeight="600" sx={{ mb: 3 }}>
              Analysis Summary
            </Typography>
            <Box sx={{ 
              display: 'grid', 
              gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, 
              gap: 3 
            }}>
              <Paper sx={{ p: 3, textAlign: 'center', backgroundColor: '#f5f5f5', border: '1px solid #e0e0e0' }}>
                <Typography variant="body1" fontWeight="500" color="text.secondary" sx={{ mb: 1 }}>
                  Competitors Found
                </Typography>
                <Typography variant="h3" component="p" fontWeight="700" color="primary.main">
                  {analysisResult.competitors?.length || 0}
                </Typography>
              </Paper>
              <Paper sx={{ p: 3, textAlign: 'center', backgroundColor: '#e8f5e8', border: '1px solid #c8e6c9' }}>
                <Typography variant="body1" fontWeight="500" color="success.main" sx={{ mb: 1 }}>
                  Status
                </Typography>
                <Typography variant="h5" component="p" fontWeight="600" color="success.main" sx={{ textTransform: 'capitalize' }}>
                  {analysisResult.status}
                </Typography>
              </Paper>
              <Paper sx={{ p: 3, textAlign: 'center', backgroundColor: '#f5f5f5', border: '1px solid #e0e0e0' }}>
                <Typography variant="body1" fontWeight="500" color="text.secondary" sx={{ mb: 1 }}>
                  Industry
                </Typography>
                <Typography variant="h5" component="p" fontWeight="600" color="text.primary">
                  {analysisResult.industry}
                </Typography>
              </Paper>
            </Box>
          </CardContent>
        </Card>

        {/* Workflow Visualization for Completed Analysis */}
        <Card sx={{ borderRadius: 2, boxShadow: 3, mb: { xs: 3, md: 4 } }}>
          <CardContent sx={{ p: { xs: 3, md: 4 } }}>
            <Typography variant="h4" component="h2" gutterBottom fontWeight="600" sx={{ mb: 3 }}>
              Analysis Process
            </Typography>
            <WorkflowVisualization 
              currentStage={analysisResult.current_stage || 'report'}
              status={analysisResult.status}
              requestId={analysisResult.request_id}
              onHumanReviewClick={() => {
                if (analysisResult.current_stage === 'human_review') {
                  setForceShowReview(true);
                }
              }}
              showTitle={false}
            />
          </CardContent>
        </Card>

        {/* Competitors */}
        {analysisResult.competitors && analysisResult.competitors.length > 0 && (
          <Card sx={{ borderRadius: 2, boxShadow: 3, mb: { xs: 3, md: 4 } }}>
            <CardContent sx={{ p: { xs: 3, md: 4 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                <Typography variant="h4" component="h2" fontWeight="600">
                  Competitors ({analysisResult.competitors.length})
                </Typography>
                <IconButton
                  onClick={() => openSectionDebug('competitors')}
                  size="small"
                  sx={{ color: 'text.secondary', '&:hover': { color: 'primary.main' } }}
                  title="View search queries used for competitor data"
                >
                  <Bug size={16} />
                </IconButton>
              </Box>
              <Box sx={{ 
                display: 'grid', 
                gridTemplateColumns: { xs: '1fr', lg: 'repeat(2, 1fr)' }, 
                gap: 3 
              }}>
                {analysisResult.competitors.map((competitor, index) => {
                  // Clean up competitor name if it looks like a raw data entry
                  const cleanName = (name: string) => {
                    // Remove common patterns like "10 Best Data", "83 Artificial Intelligence"
                    const cleaned = name.replace(/^\d+\s+(Best\s+)?/i, '');
                    // If the name is too generic or contains URL-like text, use a fallback
                    if (cleaned.toLowerCase().includes('exploring') || cleaned.toLowerCase().includes('annual report')) {
                      return `Competitor ${index + 1}`;
                    }
                    return cleaned || `Competitor ${index + 1}`;
                  };

                  return (
                    <Paper
                      key={index}
                      sx={{
                        border: '1px solid #e0e0e0',
                        borderRadius: 2,
                        p: { xs: 2, md: 3 },
                        backgroundColor: '#fafafa',
                        '&:hover': {
                          boxShadow: 2
                        }
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
                        <Typography variant="h6" component="h3" fontWeight="600">
                          {cleanName(competitor.name)}
                        </Typography>
                        {competitor.market_position && (
                          <Chip 
                            label={competitor.market_position}
                            size="small"
                            sx={{ fontSize: '0.75rem' }}
                          />
                        )}
                      </Box>
                  
                      {competitor.website && (
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                          <Typography 
                            component="a" 
                            href={competitor.website} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            variant="body2"
                            sx={{ 
                              color: 'text.secondary', 
                              textDecoration: 'none', 
                              '&:hover': { 
                                textDecoration: 'underline',
                                color: 'text.primary'
                              } 
                            }}
                          >
                            {competitor.website}
                          </Typography>
                        </Typography>
                      )}
                      
                      {competitor.description && (
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2, lineHeight: 1.6 }}>
                          {competitor.description.length > 150 
                            ? competitor.description.substring(0, 150) + '...' 
                            : competitor.description}
                        </Typography>
                      )}
                      
                      <Box sx={{ 
                        display: 'grid', 
                        gridTemplateColumns: 'repeat(2, 1fr)', 
                        gap: 2, 
                        mb: 2 
                      }}>
                        {competitor.business_model && (
                          <Box>
                            <Typography variant="caption" fontWeight="500" color="text.secondary">
                              Business Model:
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              {competitor.business_model}
                            </Typography>
                          </Box>
                        )}
                        {competitor.target_market && (
                          <Box>
                            <Typography variant="caption" fontWeight="500" color="text.secondary">
                              Target Market:
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              {competitor.target_market}
                            </Typography>
                          </Box>
                        )}
                      </Box>
                      
                      {competitor.strengths && competitor.strengths.length > 0 && (
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="caption" fontWeight="500" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                            Strengths:
                          </Typography>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {competitor.strengths.slice(0, 3).map((strength: string, idx: number) => (
                              <Chip 
                                key={idx} 
                                label={strength} 
                                size="small" 
                                color="success" 
                                variant="outlined"
                                sx={{ fontSize: '0.75rem' }}
                              />
                            ))}
                          </Box>
                        </Box>
                      )}
                    </Paper>
                  );
                })}
              </Box>
            </CardContent>
          </Card>
        )}

        {/* Market Analysis */}
        {analysisResult.market_analysis && Object.keys(analysisResult.market_analysis).length > 0 && (() => {
          // Check if we have nested structure or flat structure
          const marketData = analysisResult.market_analysis.market_data || analysisResult.market_analysis;
          console.log("marketData", marketData);
          const hasNestedStructure = analysisResult.market_analysis.market_data;
          
          // Data is properly accessible via marketData
          
          return (
            <Card sx={{ borderRadius: 2, boxShadow: 3, mb: { xs: 3, md: 4 } }}>
              <CardContent sx={{ p: { xs: 3, md: 4 } }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                  <Typography variant="h4" component="h2" fontWeight="600">
                    Market Analysis
                  </Typography>
                  <IconButton
                    onClick={() => openSectionDebug('market')}
                    size="small"
                    sx={{ color: 'text.secondary', '&:hover': { color: 'primary.main' } }}
                    title="View search queries used for market analysis"
                  >
                    <Bug size={16} />
                  </IconButton>
                </Box>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                  {/* Market Overview Cards */}
                  {(marketData.market_size || marketData.growth_trends || marketData.competitive_intensity) && (
                    <Box sx={{ 
                      display: 'grid', 
                      gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, 
                      gap: 3 
                    }}>
                      {marketData.market_size && (
                        <Paper sx={{ p: 3, backgroundColor: '#f5f5f5', border: '1px solid #e0e0e0' }}>
                          <Typography variant="h6" fontWeight="600" color="text.secondary" sx={{ mb: 1 }}>
                            Market Size
                          </Typography>
                          {typeof marketData.market_size === 'object' ? (
                            <>
                              <Typography variant="h5" component="p" fontWeight="700" color="text.primary">
                                {marketData.market_size.current_market_size}
                              </Typography>
                              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                                Growth: {marketData.market_size.growth_rate}
                              </Typography>
                            </>
                          ) : (
                            <Typography variant="body1" color="text.primary">
                              {marketData.market_size}
                            </Typography>
                          )}
                        </Paper>
                      )}
                      
                      {marketData.competitive_intensity && (
                        <Paper sx={{ p: 3, backgroundColor: '#fff3e0', border: '1px solid #ffcc02' }}>
                          <Typography variant="h6" fontWeight="600" color="warning.main" sx={{ mb: 1 }}>
                            Competition Level
                          </Typography>
                          {typeof marketData.competitive_intensity === 'object' ? (
                            <>
                              <Typography variant="h5" component="p" fontWeight="700" color="warning.dark">
                                {marketData.competitive_intensity.level}
                              </Typography>
                              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                                {marketData.competitive_intensity.explanation}
                              </Typography>
                            </>
                          ) : (
                            <Typography variant="body1" color="text.primary">
                              {marketData.competitive_intensity}
                            </Typography>
                          )}
                        </Paper>
                      )}
                      
                      {marketData.growth_trends && !Array.isArray(marketData.growth_trends) && (
                        <Paper sx={{ p: 3, backgroundColor: '#e3f2fd', border: '1px solid #2196f3' }}>
                          <Typography variant="h6" fontWeight="600" color="primary.main" sx={{ mb: 1 }}>
                            Growth Trends
                          </Typography>
                          <Typography variant="body1" color="text.primary">
                            {marketData.growth_trends}
                          </Typography>
                        </Paper>
                      )}
                    </Box>
                  )}

                  {/* Key Trends (for nested structure) */}
                  {marketData.key_trends && marketData.key_trends.length > 0 && (
                    <Paper sx={{ p: 3, backgroundColor: '#e3f2fd', border: '1px solid #2196f3' }}>
                      <Typography variant="h6" fontWeight="600" color="primary.main" sx={{ mb: 2 }}>
                        Key Market Trends
                      </Typography>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                        {(marketData.key_trends || []).map((trend: any, index: number) => (
                          <Paper key={index} sx={{ p: 2, border: '1px solid #e0e0e0' }}>
                            {typeof trend === 'string' ? (
                              <Typography variant="body1" color="text.primary">
                                {trend}
                              </Typography>
                            ) : (
                              <>
                                <Typography variant="body1" fontWeight="500" color="primary.dark" sx={{ mb: 0.5 }}>
                                  {trend.trend}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                  {trend.description}
                                </Typography>
                              </>
                            )}
                          </Paper>
                        ))}
                      </Box>
                    </Paper>
                  )}

                  {/* Opportunities and Threats (for nested structure) */}
                  {(marketData.opportunities || marketData.threats) && (
                    <Box sx={{ 
                      display: 'grid', 
                      gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, 
                      gap: 3 
                    }}>
                      {marketData.opportunities && marketData.opportunities.length > 0 && (
                        <Paper sx={{ p: 3, backgroundColor: '#e8f5e8', border: '1px solid #4caf50' }}>
                          <Typography variant="h6" fontWeight="600" color="success.main" sx={{ mb: 2 }}>
                            Market Opportunities
                          </Typography>
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                            {(marketData.opportunities || []).map((opp: any, index: number) => (
                              <Paper key={index} sx={{ p: 2, border: '1px solid #e0e0e0' }}>
                                {typeof opp === 'string' ? (
                                  <Typography variant="body1" color="text.primary">
                                    {opp}
                                  </Typography>
                                ) : (
                                  <>
                                    <Typography variant="body1" fontWeight="500" color="success.dark" sx={{ mb: 0.5 }}>
                                      {opp.opportunity}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                      {opp.description}
                                    </Typography>
                                  </>
                                )}
                              </Paper>
                            ))}
                          </Box>
                        </Paper>
                      )}

                      {marketData.threats && marketData.threats.length > 0 && (
                        <Paper sx={{ p: 3, backgroundColor: '#ffebee', border: '1px solid #f44336' }}>
                          <Typography variant="h6" fontWeight="600" color="error.main" sx={{ mb: 2 }}>
                            Market Threats
                          </Typography>
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                            {(marketData.threats || []).map((threat: any, index: number) => (
                              <Paper key={index} sx={{ p: 2, border: '1px solid #e0e0e0' }}>
                                {typeof threat === 'string' ? (
                                  <Typography variant="body1" color="text.primary">
                                    {threat}
                                  </Typography>
                                ) : (
                                  <>
                                    <Typography variant="body1" fontWeight="500" color="error.dark" sx={{ mb: 0.5 }}>
                                      {threat.threat}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                      {threat.description}
                                    </Typography>
                                  </>
                                )}
                              </Paper>
                            ))}
                          </Box>
                        </Paper>
                      )}
                    </Box>
                  )}

                  {/* Key Players */}
                  {marketData.key_players && marketData.key_players.length > 0 && (
                    <Paper sx={{ p: 3, backgroundColor: '#fff3e0', border: '1px solid #ffcc80' }}>
                      <Typography variant="h6" fontWeight="600" color="warning.dark" sx={{ mb: 2 }}>
                        Key Market Players
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {marketData.key_players.map((player: string, index: number) => (
                          <Chip 
                            key={index}
                            label={player}
                            sx={{ fontWeight: 500 }}
                            color="warning"
                            variant="outlined"
                          />
                        ))}
                      </Box>
                    </Paper>
                  )}

                  {/* Market Segments */}
                  {marketData.market_segments && (
                    <Paper sx={{ p: 3, backgroundColor: '#f5f5f5', border: '1px solid #e0e0e0' }}>
                      <Typography variant="h6" fontWeight="600" color="text.secondary" sx={{ mb: 1 }}>
                        Market Segments
                      </Typography>
                      <Typography variant="body1" color="text.primary">
                        {marketData.market_segments}
                      </Typography>
                    </Paper>
                  )}

                  {/* Competitive Dynamics */}
                  {marketData.competitive_dynamics && (
                    <Paper sx={{ p: 3, backgroundColor: '#fce4ec', border: '1px solid #f8bbd0' }}>
                      <Typography variant="h6" fontWeight="600" color="secondary.main" sx={{ mb: 1 }}>
                        Competitive Dynamics
                      </Typography>
                      <Typography variant="body1" color="text.primary">
                        {marketData.competitive_dynamics}
                      </Typography>
                    </Paper>
                  )}

                  {/* Market Outlook */}
                  {marketData.outlook && (
                    <Paper sx={{ p: 3, backgroundColor: '#f5f5f5', border: '1px solid #e0e0e0' }}>
                      <Typography variant="h6" fontWeight="600" color="text.primary" sx={{ mb: 2 }}>
                        Market Outlook
                      </Typography>
                      {marketData.outlook['12_month_market_outlook'] ? (
                        <Box>
                          <Typography variant="body1" fontWeight="500" color="text.primary" sx={{ mb: 1 }}>
                            12-Month Outlook
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {marketData.outlook['12_month_market_outlook']}
                          </Typography>
                        </Box>
                      ) : typeof marketData.outlook === 'string' ? (
                        <Typography variant="body1" color="text.primary">
                          {marketData.outlook}
                        </Typography>
                      ) : (
                        <Typography variant="body1" color="text.primary">
                          {JSON.stringify(marketData.outlook)}
                        </Typography>
                      )}
                    </Paper>
                  )}
                </Box>
              </CardContent>
            </Card>
          );
        })()}

        {/* Threats & Opportunities (separate section for flat structure) */}
        {analysisResult.threats_opportunities && 
         analysisResult.threats_opportunities.opportunities && 
         analysisResult.threats_opportunities.threats && (
          <Card sx={{ borderRadius: 2, boxShadow: 3, mb: { xs: 3, md: 4 } }}>
            <CardContent sx={{ p: { xs: 3, md: 4 } }}>
              <Typography variant="h4" component="h2" fontWeight="600" sx={{ mb: 3 }}>
                Threats & Opportunities
              </Typography>
              <Box sx={{ 
                display: 'grid', 
                gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, 
                gap: 3 
              }}>
                {/* Opportunities */}
                {analysisResult.threats_opportunities.opportunities && analysisResult.threats_opportunities.opportunities.length > 0 && (
                  <Paper sx={{ p: 3, backgroundColor: '#e8f5e9', border: '1px solid #4caf50' }}>
                    <Typography variant="h6" fontWeight="600" color="success.main" sx={{ mb: 2 }}>
                      Opportunities
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      {analysisResult.threats_opportunities.opportunities.map((opp: string, index: number) => (
                        <Box key={index} sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                          <Typography variant="body2" color="success.main" sx={{ mt: 0.5 }}>•</Typography>
                          <Typography variant="body1" color="text.primary">
                            {opp}
                          </Typography>
                        </Box>
                      ))}
                    </Box>
                  </Paper>
                )}

                {/* Threats */}
                {analysisResult.threats_opportunities.threats && analysisResult.threats_opportunities.threats.length > 0 && (
                  <Paper sx={{ p: 3, backgroundColor: '#ffebee', border: '1px solid #f44336' }}>
                    <Typography variant="h6" fontWeight="600" color="error.main" sx={{ mb: 2 }}>
                      Threats
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      {analysisResult.threats_opportunities.threats.map((threat: string, index: number) => (
                        <Box key={index} sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                          <Typography variant="body2" color="error.main" sx={{ mt: 0.5 }}>•</Typography>
                          <Typography variant="body1" color="text.primary">
                            {threat}
                          </Typography>
                        </Box>
                      ))}
                    </Box>
                  </Paper>
                )}
              </Box>
            </CardContent>
          </Card>
        )}

        {/* Recommendations */}
        {analysisResult.recommendations && analysisResult.recommendations.length > 0 && (
          <Card sx={{ borderRadius: 2, boxShadow: 3 }}>
            <CardContent sx={{ p: { xs: 3, md: 4 } }}>
              <Typography variant="h4" component="h2" fontWeight="600" sx={{ mb: 3 }}>
                Strategic Recommendations ({analysisResult.recommendations.length})
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                {analysisResult.recommendations.map((rec, index) => (
                  <Paper 
                    key={index} 
                    sx={{ 
                      background: 'linear-gradient(to right, #fff8e1, #ffecb3)',
                      borderLeft: '4px solid #ffc107',
                      borderRadius: '0 8px 8px 0',
                      p: 3
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                      <Box sx={{
                        flexShrink: 0,
                        width: 24,
                        height: 24,
                        backgroundColor: 'warning.main',
                        color: 'white',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.875rem',
                        fontWeight: 'bold',
                        mt: 0.25
                      }}>
                        {index + 1}
                      </Box>
                      <Typography variant="body1" color="text.primary" sx={{ lineHeight: 1.6 }}>
                        {rec}
                      </Typography>
                    </Box>
                  </Paper>
                ))}
              </Box>
            </CardContent>
          </Card>
        )}
        </Container>

        {/* Debug Modal */}
      <Modal
        open={!!debugModalSection}
        onClose={() => setDebugModalSection(null)}
        sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          p: 2
        }}
      >
        <Card sx={{ 
          borderRadius: 2, 
          boxShadow: 3, 
          maxWidth: 600, 
          width: '100%', 
          maxHeight: '90vh', 
          overflow: 'hidden' 
        }}>
          <CardContent sx={{ p: 0 }}>
            <Box sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'space-between', 
              p: 3, 
              borderBottom: '1px solid #e0e0e0' 
            }}>
              <Typography variant="h6" fontWeight="600" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Bug size={20} color="#1976d2" />
                {debugModalSection === 'competitors' ? 'Competitor Search Queries' : 
                 debugModalSection === 'market' ? 'Market Analysis Queries' : 'Search Queries'}
              </Typography>
              <IconButton
                onClick={() => setDebugModalSection(null)}
                size="small"
              >
                <X size={20} />
              </IconButton>
            </Box>
          
            <Box sx={{ p: 3, overflowY: 'auto', maxHeight: 'calc(90vh - 120px)' }}>
              {(() => {
                const sectionLogs = getSectionSearchLogs(debugModalSection || '');
                
                if (searchLogs.length === 0) {
                  return (
                    <Box sx={{ textAlign: 'center', py: 4 }}>
                      <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                        No search logs available
                      </Typography>
                      <Button
                        onClick={loadSearchLogs}
                        variant="contained"
                        sx={{ textTransform: 'none' }}
                      >
                        Load Search Logs
                      </Button>
                    </Box>
                  );
                }

                if (sectionLogs.length === 0) {
                  return (
                    <Box sx={{ textAlign: 'center', py: 4 }}>
                      <Typography variant="body1" color="text.secondary">
                        No search queries found for this section
                      </Typography>
                    </Box>
                  );
                }

                return (
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Showing {sectionLogs.length} search quer{sectionLogs.length === 1 ? 'y' : 'ies'} used to populate this section:
                    </Typography>
                    
                    {sectionLogs.map((log, index) => (
                      <Paper key={index} sx={{ border: '1px solid #e0e0e0', borderRadius: 2, p: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                          <Typography variant="h6" sx={{ flexShrink: 0, mt: 0.5 }}>
                            {log.search_type === 'competitor_search' ? '🏢' : 
                             log.search_type === 'company_details' ? '📋' : 
                             log.search_type === 'market_analysis' ? '📊' : '🔍'}
                          </Typography>
                          <Box sx={{ flex: 1 }}>
                            <Typography variant="body1" fontWeight="500" sx={{ mb: 1 }}>
                              {log.search_type.replace('_', ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
                            </Typography>
                            <Paper sx={{ 
                              fontFamily: 'monospace', 
                              fontSize: '0.875rem', 
                              backgroundColor: '#f5f5f5', 
                              p: 1.5, 
                              border: '1px solid #e0e0e0' 
                            }}>
                              "{log.query}"
                            </Paper>
                          </Box>
                        </Box>
                      </Paper>
                    ))}
                  </Box>
                );
              })()}
            </Box>
          </CardContent>
        </Card>
      </Modal>
    </Box>
  );
};

export default ResultsPageV2;
