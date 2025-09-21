import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  FileText, 
  Search, 
  Filter, 
  Download, 
  Eye,
  Calendar,
  Building2,
  TrendingUp,
  Users,
  ChevronRight,
  RefreshCw,
  Loader,
  Database,
  Brain,
  BarChart3,
  Shield,
  ArrowRight,
  PlayCircle,
  CheckCircle,
  Globe
} from 'lucide-react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Chip,
  Paper,
  Tabs,
  Tab,
  LinearProgress,
  alpha
} from '@mui/material';
import { reportsAPI, analysisAPI } from '../services/api';

interface Report {
  id: string;
  analysis_id: string;
  title: string;
  client_company: string;
  industry: string;
  analysis_date: string;
  total_competitors_analyzed: number;
  confidence_level: string;
  created_at: string;
}

interface Analysis {
  request_id: string;
  client_company: string;
  industry: string;
  status: string;
  created_at: string;
  competitors: any[];
  market_analysis?: any;
  competitive_landscape?: any;
  recommendations?: string[];
  progress?: number;
  error_message?: string;
}

const ReportsPage: React.FC = () => {
  const [reports, setReports] = useState<Report[]>([]);
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterIndustry, setFilterIndustry] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [activeTab, setActiveTab] = useState<'reports' | 'analyses'>('analyses');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load both reports and analyses
      const [reportsResponse, analysesResponse] = await Promise.all([
        reportsAPI.listReports().catch(() => ({ data: [] })), // Graceful fallback
        analysisAPI.listAnalyses()
      ]);

      setReports(reportsResponse.data || []);
      setAnalyses(analysesResponse.data || []);

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  // Get unique industries for filter dropdown
  const industries = Array.from(
    new Set([
      ...reports.map(r => r.industry),
      ...analyses.map(a => a.industry)
    ])
  ).filter(Boolean);

  // Filter reports based on search and filters
  const filteredReports = reports.filter(report => {
    const matchesSearch = 
      report.client_company.toLowerCase().includes(searchTerm.toLowerCase()) ||
      report.title.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesIndustry = !filterIndustry || report.industry === filterIndustry;
    
    return matchesSearch && matchesIndustry;
  });

  // Filter analyses based on search and filters
  const filteredAnalyses = analyses.filter(analysis => {
    const matchesSearch = 
      analysis.client_company.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesIndustry = !filterIndustry || analysis.industry === filterIndustry;
    const matchesStatus = !filterStatus || analysis.status === filterStatus;
    
    return matchesSearch && matchesIndustry && matchesStatus;
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <Box sx={{ 
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        py: { xs: 2, md: 4 },
        px: { xs: 2, md: 3 }
      }}>
        <Container maxWidth="xl">
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', py: 12 }}>
            <Loader className="animate-spin mr-3" size={32} color="white" />
            <Typography variant="h6" sx={{ color: 'white' }}>
              Loading reports...
            </Typography>
          </Box>
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
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: { xs: 4, md: 6 } }}>
          <Box>
            <Typography 
              variant="h3" 
              component="h1" 
              gutterBottom 
              fontWeight="bold"
              sx={{ color: 'white', mb: 2 }}
            >
              Reports & Analyses
            </Typography>
            <Typography 
              variant="h6" 
              component="p" 
              sx={{ color: 'rgba(255, 255, 255, 0.9)' }}
            >
              Browse and manage your competitive analysis reports
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Button 
              onClick={loadData}
              variant="outlined"
              startIcon={<RefreshCw size={16} />}
              sx={{ 
                color: 'white',
                borderColor: 'rgba(255, 255, 255, 0.5)',
                '&:hover': {
                  borderColor: 'white',
                  backgroundColor: 'rgba(255, 255, 255, 0.1)'
                }
              }}
            >
              Refresh
            </Button>
            <Button
              component={Link}
              to="/analysis"
              variant="contained"
              sx={{ 
                backgroundColor: 'white',
                color: 'primary.main',
                '&:hover': {
                  backgroundColor: 'grey.100'
                }
              }}
            >
              New Analysis
            </Button>
            <Button
              component={Link}
              to="/home"
              variant="outlined"
              sx={{ 
                color: 'white',
                borderColor: 'rgba(255, 255, 255, 0.5)',
                '&:hover': {
                  borderColor: 'white',
                  backgroundColor: 'rgba(255, 255, 255, 0.1)'
                }
              }}
            >
              Back to Dashboard
            </Button>
          </Box>
        </Box>

        {/* Error Message */}
        {error && (
          <Alert 
            severity="error" 
            sx={{ mb: { xs: 3, md: 4 }, borderRadius: 2 }}
          >
            <Typography variant="h6" component="h3" sx={{ fontWeight: 600, mb: 1 }}>
              Error Loading Data
            </Typography>
            <Typography variant="body2">
              {error}
            </Typography>
          </Alert>
        )}

        {/* Search and Filters */}
        <Card sx={{ borderRadius: 2, boxShadow: 3, mb: { xs: 3, md: 4 } }}>
          <CardContent sx={{ p: { xs: 3, md: 4 } }}>
            <Box sx={{ 
              display: 'flex', 
              flexDirection: { xs: 'column', md: 'row' }, 
              gap: 2 
            }}>
              {/* Search */}
              <Box sx={{ flex: 1, position: 'relative' }}>
                <Search size={20} style={{ 
                  position: 'absolute', 
                  left: 12, 
                  top: '50%', 
                  transform: 'translateY(-50%)', 
                  color: '#9e9e9e' 
                }} />
                <TextField
                  fullWidth
                  placeholder="Search by company name or report title..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      paddingLeft: '40px'
                    }
                  }}
                />
              </Box>

              {/* Industry Filter */}
              <FormControl sx={{ minWidth: 200 }}>
                <InputLabel>Industry</InputLabel>
                <Select
                  value={filterIndustry}
                  label="Industry"
                  onChange={(e) => setFilterIndustry(e.target.value)}
                >
                  <MenuItem value="">All Industries</MenuItem>
                  {industries.map(industry => (
                    <MenuItem key={industry} value={industry}>
                      {industry}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Status Filter (for analyses) */}
              {activeTab === 'analyses' && (
                <FormControl sx={{ minWidth: 150 }}>
                  <InputLabel>Status</InputLabel>
                  <Select
                    value={filterStatus}
                    label="Status"
                    onChange={(e) => setFilterStatus(e.target.value)}
                  >
                    <MenuItem value="">All Status</MenuItem>
                    <MenuItem value="completed">Completed</MenuItem>
                    <MenuItem value="in_progress">In Progress</MenuItem>
                    <MenuItem value="failed">Failed</MenuItem>
                    <MenuItem value="pending">Pending</MenuItem>
                  </Select>
                </FormControl>
              )}
            </Box>
          </CardContent>
        </Card>

        {/* Tabs */}
        <Paper sx={{ 
          display: 'flex', 
          borderRadius: 2, 
          p: 0.5, 
          mb: { xs: 3, md: 4 }, 
          width: 'fit-content',
          backgroundColor: 'white'
        }}>
          <Button
            onClick={() => setActiveTab('analyses')}
            variant={activeTab === 'analyses' ? 'contained' : 'text'}
            sx={{
              px: 3,
              py: 1.5,
              borderRadius: 1.5,
              fontWeight: 600,
              textTransform: 'none',
              ...(activeTab === 'analyses' ? {
                backgroundColor: 'primary.main',
                color: 'white'
              } : {
                color: 'text.secondary',
                '&:hover': {
                  color: 'primary.main',
                  backgroundColor: 'transparent'
                }
              })
            }}
          >
            Analyses ({filteredAnalyses.length})
          </Button>
          <Button
            onClick={() => setActiveTab('reports')}
            variant={activeTab === 'reports' ? 'contained' : 'text'}
            sx={{
              px: 3,
              py: 1.5,
              borderRadius: 1.5,
              fontWeight: 600,
              textTransform: 'none',
              ...(activeTab === 'reports' ? {
                backgroundColor: 'primary.main',
                color: 'white'
              } : {
                color: 'text.secondary',
                '&:hover': {
                  color: 'primary.main',
                  backgroundColor: 'transparent'
                }
              })
            }}
          >
            Reports ({filteredReports.length})
          </Button>
        </Paper>

        {/* Content */}
        {activeTab === 'analyses' ? (
          /* Analyses List */
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {filteredAnalyses.length > 0 ? (
              filteredAnalyses.map((analysis) => (
                <Card key={analysis.request_id} sx={{ borderRadius: 2, boxShadow: 3, transition: 'all 0.2s', '&:hover': { boxShadow: 6 } }}>
                  <CardContent sx={{ p: { xs: 3, md: 4 } }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexDirection: { xs: 'column', md: 'row' }, gap: 2 }}>
                      <Box sx={{ flex: 1, width: '100%' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2, flexWrap: 'wrap' }}>
                          <Typography variant="h5" component="h3" fontWeight="600">
                            {analysis.client_company}
                          </Typography>
                          <Chip 
                            label={analysis.status.replace('_', ' ')}
                            size="small"
                            color={analysis.status === 'completed' ? 'success' : analysis.status === 'in_progress' ? 'warning' : 'error'}
                            sx={{ textTransform: 'capitalize', fontWeight: 500 }}
                          />
                        </Box>
                        
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 4, mb: 3, flexWrap: 'wrap' }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Building2 size={16} color="#666" />
                            <Typography variant="body2" color="text.secondary">
                              {analysis.industry}
                            </Typography>
                          </Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Users size={16} color="#666" />
                            <Typography variant="body2" color="text.secondary">
                              {analysis.competitors?.length || 0} competitors
                            </Typography>
                          </Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Calendar size={16} color="#666" />
                            <Typography variant="body2" color="text.secondary">
                              {formatDate(analysis.created_at)}
                            </Typography>
                          </Box>
                        </Box>
                        
                        {/* Agent Progress Details */}
                        {analysis.status === 'completed' && (
                          <Paper sx={{ mt: 2, p: 2, backgroundColor: 'grey.50', borderRadius: 2 }}>
                            <Typography variant="body2" fontWeight="600" color="text.secondary" sx={{ mb: 2 }}>
                              What was accomplished:
                            </Typography>
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5 }}>
                                <Box sx={{ width: 6, height: 6, backgroundColor: 'success.main', borderRadius: '50%', mt: 0.5 }} />
                                <Box>
                                  <Typography variant="caption" fontWeight="500">
                                    Search & Discovery:
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                                    {analysis.competitors?.length || 0} competitors found
                                  </Typography>
                                </Box>
                              </Box>
                              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5 }}>
                                <Box sx={{ width: 6, height: 6, backgroundColor: 'success.main', borderRadius: '50%', mt: 0.5 }} />
                                <Box>
                                  <Typography variant="caption" fontWeight="500">
                                    AI Analysis:
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                                    {analysis.market_analysis ? 'Market insights generated' : 'Pending'}
                                  </Typography>
                                </Box>
                              </Box>
                              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5 }}>
                                <Box sx={{ width: 6, height: 6, backgroundColor: 'success.main', borderRadius: '50%', mt: 0.5 }} />
                                <Box>
                                  <Typography variant="caption" fontWeight="500">
                                    Quality Assurance:
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                                    {analysis.competitive_landscape ? 'Data validated' : 'Pending'}
                                  </Typography>
                                </Box>
                              </Box>
                              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5 }}>
                                <Box sx={{ width: 6, height: 6, backgroundColor: 'success.main', borderRadius: '50%', mt: 0.5 }} />
                                <Box>
                                  <Typography variant="caption" fontWeight="500">
                                    Report Generation:
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                                    {analysis.recommendations?.length || 0} recommendations
                                  </Typography>
                                </Box>
                              </Box>
                            </Box>
                          </Paper>
                        )}
                        
                        {/* In-Progress Status */}
                        {analysis.status === 'in_progress' && (
                          <Paper sx={{ mt: 2, p: 2, backgroundColor: 'info.50', borderRadius: 2 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                              <Loader className="animate-spin" size={16} color="#1976d2" />
                              <Typography variant="body2" color="info.main">
                                Analysis in progress... {analysis.progress || 0}% complete
                              </Typography>
                            </Box>
                          </Paper>
                        )}
                        
                        {/* Failed Status */}
                        {analysis.status === 'failed' && (
                          <Paper sx={{ mt: 2, p: 2, backgroundColor: 'error.50', borderRadius: 2 }}>
                            <Typography variant="body2" color="error.main">
                              Analysis failed: {analysis.error_message || 'Unknown error'}
                            </Typography>
                          </Paper>
                        )}
                      </Box>

                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexDirection: { xs: 'row', md: 'column' } }}>
                        {analysis.status === 'completed' && (
                          <Button
                            variant="outlined"
                            startIcon={<Download size={16} />}
                            sx={{ textTransform: 'none', fontWeight: 600 }}
                          >
                            Export
                          </Button>
                        )}
                        
                        <Button
                          component={Link}
                          to={`/results/${analysis.request_id}`}
                          variant="contained"
                          startIcon={<Eye size={16} />}
                          endIcon={<ChevronRight size={16} />}
                          sx={{ textTransform: 'none', fontWeight: 600 }}
                        >
                          View
                        </Button>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              ))
            ) : (
              <Card sx={{ borderRadius: 2, boxShadow: 3 }}>
                <CardContent sx={{ p: { xs: 6, md: 8 }, textAlign: 'center' }}>
                  <FileText size={64} color="#9e9e9e" style={{ marginBottom: 16 }} />
                  <Typography variant="h5" component="h3" fontWeight="600" sx={{ mb: 2 }}>
                    No Analyses Found
                  </Typography>
                  <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
                    {searchTerm || filterIndustry || filterStatus
                      ? 'No analyses match your current filters.'
                      : 'You haven\'t created any analyses yet.'}
                  </Typography>
                  <Button
                    component={Link}
                    to="/analysis"
                    variant="contained"
                    sx={{ textTransform: 'none', fontWeight: 600 }}
                  >
                    Create Your First Analysis
                  </Button>
                </CardContent>
              </Card>
            )}
          </Box>
        ) : (
          /* Reports List */
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {filteredReports.length > 0 ? (
              filteredReports.map((report) => (
                <Card key={report.id} sx={{ borderRadius: 2, boxShadow: 3, transition: 'all 0.2s', '&:hover': { boxShadow: 6 } }}>
                  <CardContent sx={{ p: { xs: 3, md: 4 } }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexDirection: { xs: 'column', md: 'row' }, gap: 2 }}>
                      <Box sx={{ flex: 1, width: '100%' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2, flexWrap: 'wrap' }}>
                          <Typography variant="h5" component="h3" fontWeight="600">
                            {report.title}
                          </Typography>
                          <Chip 
                            label={`${report.confidence_level} confidence`}
                            size="small"
                            color={report.confidence_level?.toLowerCase() === 'high' ? 'success' : report.confidence_level?.toLowerCase() === 'medium' ? 'warning' : 'error'}
                            sx={{ textTransform: 'capitalize', fontWeight: 500 }}
                          />
                        </Box>
                        
                        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                          Competitive analysis for {report.client_company} in {report.industry}
                        </Typography>
                        
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 4, flexWrap: 'wrap' }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Building2 size={16} color="#666" />
                            <Typography variant="body2" color="text.secondary">
                              {report.industry}
                            </Typography>
                          </Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Users size={16} color="#666" />
                            <Typography variant="body2" color="text.secondary">
                              {report.total_competitors_analyzed} competitors
                            </Typography>
                          </Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Calendar size={16} color="#666" />
                            <Typography variant="body2" color="text.secondary">
                              {formatDate(report.analysis_date)}
                            </Typography>
                          </Box>
                        </Box>
                      </Box>

                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexDirection: { xs: 'row', md: 'column' } }}>
                        <Button
                          variant="outlined"
                          startIcon={<Download size={16} />}
                          sx={{ textTransform: 'none', fontWeight: 600 }}
                        >
                          Download
                        </Button>
                        
                        <Button
                          variant="contained"
                          startIcon={<Eye size={16} />}
                          endIcon={<ChevronRight size={16} />}
                          sx={{ textTransform: 'none', fontWeight: 600 }}
                        >
                          View Report
                        </Button>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              ))
            ) : (
              <Card sx={{ borderRadius: 2, boxShadow: 3 }}>
                <CardContent sx={{ p: { xs: 6, md: 8 }, textAlign: 'center' }}>
                  <FileText size={64} color="#9e9e9e" style={{ marginBottom: 16 }} />
                  <Typography variant="h5" component="h3" fontWeight="600" sx={{ mb: 2 }}>
                    No Reports Found
                  </Typography>
                  <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
                    {searchTerm || filterIndustry
                      ? 'No reports match your current filters.'
                      : 'No reports have been generated yet.'}
                  </Typography>
                  <Button
                    component={Link}
                    to="/analysis"
                    variant="contained"
                    sx={{ textTransform: 'none', fontWeight: 600 }}
                  >
                    Create Analysis to Generate Reports
                  </Button>
                </CardContent>
              </Card>
            )}
          </Box>
        )}

        {/* Summary Stats */}
        {(filteredAnalyses.length > 0 || filteredReports.length > 0) && (
          <Box sx={{ 
            mt: 8, 
            display: 'grid', 
            gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, 
            gap: 3 
          }}>
            <Card sx={{ borderRadius: 2, boxShadow: 3 }}>
              <CardContent sx={{ p: { xs: 3, md: 4 }, textAlign: 'center' }}>
                <Paper sx={{ 
                  width: 48, 
                  height: 48, 
                  borderRadius: '50%', 
                  backgroundColor: 'primary.50',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  mx: 'auto',
                  mb: 2
                }}>
                  <FileText size={24} color="#1976d2" />
                </Paper>
                <Typography variant="h4" component="h3" fontWeight="700" sx={{ mb: 1 }}>
                  {analyses.length}
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Total Analyses
                </Typography>
              </CardContent>
            </Card>

            <Card sx={{ borderRadius: 2, boxShadow: 3 }}>
              <CardContent sx={{ p: { xs: 3, md: 4 }, textAlign: 'center' }}>
                <Paper sx={{ 
                  width: 48, 
                  height: 48, 
                  borderRadius: '50%', 
                  backgroundColor: 'success.50',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  mx: 'auto',
                  mb: 2
                }}>
                  <TrendingUp size={24} color="#2e7d32" />
                </Paper>
                <Typography variant="h4" component="h3" fontWeight="700" sx={{ mb: 1 }}>
                  {analyses.filter(a => a.status === 'completed').length}
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Completed
                </Typography>
              </CardContent>
            </Card>

            <Card sx={{ borderRadius: 2, boxShadow: 3 }}>
              <CardContent sx={{ p: { xs: 3, md: 4 }, textAlign: 'center' }}>
                <Paper sx={{ 
                  width: 48, 
                  height: 48, 
                  borderRadius: '50%', 
                  backgroundColor: 'warning.50',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  mx: 'auto',
                  mb: 2
                }}>
                  <Building2 size={24} color="#ed6c02" />
                </Paper>
                <Typography variant="h4" component="h3" fontWeight="700" sx={{ mb: 1 }}>
                  {industries.length}
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Industries
                </Typography>
              </CardContent>
            </Card>
          </Box>
        )}
      </Container>
    </Box>
  );
};

export default ReportsPage;