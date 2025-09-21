import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  BarChart3, 
  Search, 
  FileText, 
  Users, 
  TrendingUp, 
  Shield,
  ChevronRight,
  Clock,
  CheckCircle,
  Loader
} from 'lucide-react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  Grid,
  Paper,
  Chip
} from '@mui/material';
import { analysisAPI } from '../services/api';

interface RecentAnalysis {
  request_id: string;
  client_company: string;
  industry: string;
  status: string;
  created_at: string;
  progress: number;
}

const HomePage: React.FC = () => {
  const [recentAnalyses, setRecentAnalyses] = useState<RecentAnalysis[]>([]);
  const [stats, setStats] = useState({
    totalAnalyses: 0,
    completedToday: 0,
    activeAnalyses: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load recent analyses for the recent analyses section
      const recentAnalysesResponse = await analysisAPI.listAnalyses({ limit: 5 });
      setRecentAnalyses(recentAnalysesResponse.data);
      
      // Load ALL analyses to calculate accurate stats
      const allAnalysesResponse = await analysisAPI.listAnalyses({ limit: 1000 }); // Get up to 1000 analyses
      const allAnalyses = allAnalysesResponse.data;
      
      // Calculate accurate stats from all analyses
      const totalAnalyses = allAnalyses.length;
      const completedToday = allAnalyses.filter((a: RecentAnalysis) => {
        const today = new Date().toDateString();
        const analysisDate = new Date(a.created_at).toDateString();
        return analysisDate === today && a.status === 'completed';
      }).length;
      const activeAnalyses = allAnalyses.filter((a: RecentAnalysis) => 
        a.status === 'in_progress'
      ).length;
      
      setStats({
        totalAnalyses,
        completedToday,
        activeAnalyses
      });
      
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle size={20} color="#4caf50" />;
      case 'in_progress':
        return <Clock size={20} color="#ff9800" />;
      default:
        return <Clock size={20} color="#9e9e9e" />;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Box sx={{ 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      py: { xs: 2, md: 2 },
      px: { xs: 2, md: 3 }
    }}>
      <Container maxWidth="xl">
        {/* Hero Section */}
        <Box sx={{ textAlign: 'center', mb: { xs: 3, md: 4 }, py: { xs: 1, md: 2 } }}>
          <Typography 
            variant="h2" 
            component="h1" 
            gutterBottom 
            fontWeight="bold"
            sx={{ color: 'white', mb: 3 }}
          >
            AI-Powered Competitive Analysis
          </Typography>
          <Typography 
            variant="h5" 
            component="p" 
            sx={{ color: 'rgba(255, 255, 255, 0.9)', mb: 2, maxWidth: '800px', mx: 'auto' }}
          >
            Discover insights about your competitors using advanced multi-agent AI workflows
          </Typography>
          <Button
            component={Link}
            to="/analysis"
            variant="contained"
            size="large"
            startIcon={<Search size={24} />}
            endIcon={<ChevronRight size={20} />}
            sx={{ 
              fontSize: '1.125rem',
              px: 4,
              py: 2,
              borderRadius: 2,
              textTransform: 'none',
              fontWeight: 600,
              backgroundColor: 'white',
              color: 'primary.main',
              '&:hover': {
                backgroundColor: 'grey.100'
              }
            }}
          >
            Start New Analysis
          </Button>
        </Box>


        {/* Stats Cards */}
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, 
          gap: 4, 
          mb: { xs: 6, md: 8 },
          maxWidth: '1200px',
          mx: 'auto'
        }}>
          <Card sx={{ borderRadius: 2, boxShadow: 3 }}>
            <CardContent sx={{ p: { xs: 3, md: 4 }, textAlign: 'center' }}>
              <Paper sx={{ 
                width: 64, 
                height: 64, 
                borderRadius: '50%', 
                backgroundColor: 'primary.main',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mx: 'auto',
                mb: 3
              }}>
                <BarChart3 size={32} color="white" />
              </Paper>
              <Typography variant="h2" component="div" sx={{ color: 'primary.main', fontWeight: 700, mb: 1 }}>
                {loading ? <Loader className="animate-spin" size={24} /> : stats.totalAnalyses}
              </Typography>
              <Typography variant="body1" color="text.secondary" fontWeight="500">
                Total Analyses
              </Typography>
            </CardContent>
          </Card>

          <Card sx={{ borderRadius: 2, boxShadow: 3 }}>
            <CardContent sx={{ p: { xs: 3, md: 4 }, textAlign: 'center' }}>
              <Paper sx={{ 
                width: 64, 
                height: 64, 
                borderRadius: '50%', 
                backgroundColor: 'success.main',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mx: 'auto',
                mb: 3
              }}>
                <CheckCircle size={32} color="white" />
              </Paper>
              <Typography variant="h2" component="div" sx={{ color: 'success.main', fontWeight: 700, mb: 1 }}>
                {loading ? <Loader className="animate-spin" size={24} /> : stats.completedToday}
              </Typography>
              <Typography variant="body1" color="text.secondary" fontWeight="500">
                Completed Today
              </Typography>
            </CardContent>
          </Card>

          <Card sx={{ borderRadius: 2, boxShadow: 3 }}>
            <CardContent sx={{ p: { xs: 3, md: 4 }, textAlign: 'center' }}>
              <Paper sx={{ 
                width: 64, 
                height: 64, 
                borderRadius: '50%', 
                backgroundColor: 'warning.main',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mx: 'auto',
                mb: 3
              }}>
                <Clock size={32} color="white" />
              </Paper>
              <Typography variant="h2" component="div" sx={{ color: 'warning.main', fontWeight: 700, mb: 1 }}>
                {loading ? <Loader className="animate-spin" size={24} /> : stats.activeAnalyses}
              </Typography>
              <Typography variant="body1" color="text.secondary" fontWeight="500">
                Active Analyses
              </Typography>
            </CardContent>
          </Card>
        </Box>

        {/* Features Section */}
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' }, 
          gap: 4, 
          mb: { xs: 6, md: 8 } 
        }}>
            <Card sx={{ borderRadius: 2, boxShadow: 3, height: '100%' }}>
              <CardContent sx={{ p: { xs: 3, md: 4 } }}>
                <Typography variant="h4" component="h2" gutterBottom fontWeight="600" sx={{ mb: 4 }}>
                  Powerful Features
                </Typography>
                
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 3 }}>
                    <Paper sx={{ 
                      p: 1.5, 
                      borderRadius: 2, 
                      backgroundColor: 'primary.50',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <Users size={24} color="#1976d2" />
                    </Paper>
                    <Box>
                      <Typography variant="h6" component="h3" gutterBottom fontWeight="600">
                        Multi-Agent Discovery
                      </Typography>
                      <Typography variant="body1" color="text.secondary">
                        Our AI agents work together to discover and analyze competitors 
                        across multiple data sources and market segments.
                      </Typography>
                    </Box>
                  </Box>

                  <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 3 }}>
                    <Paper sx={{ 
                      p: 1.5, 
                      borderRadius: 2, 
                      backgroundColor: 'primary.50',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <TrendingUp size={24} color="#1976d2" />
                    </Paper>
                    <Box>
                      <Typography variant="h6" component="h3" gutterBottom fontWeight="600">
                        Market Intelligence
                      </Typography>
                      <Typography variant="body1" color="text.secondary">
                        Get deep insights into market trends, competitor positioning, 
                        and strategic opportunities in your industry.
                      </Typography>
                    </Box>
                  </Box>

                  <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 3 }}>
                    <Paper sx={{ 
                      p: 1.5, 
                      borderRadius: 2, 
                      backgroundColor: 'primary.50',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <Shield size={24} color="#1976d2" />
                    </Paper>
                    <Box>
                      <Typography variant="h6" component="h3" gutterBottom fontWeight="600">
                        Quality Assurance
                      </Typography>
                      <Typography variant="body1" color="text.secondary">
                        Advanced quality checks ensure reliable and accurate 
                        competitive intelligence for strategic decision making.
                      </Typography>
                    </Box>
                  </Box>
                </Box>
              </CardContent>
            </Card>

            <Card sx={{ borderRadius: 2, boxShadow: 3, height: '100%' }}>
              <CardContent sx={{ p: { xs: 3, md: 4 } }}>
                <Typography variant="h4" component="h2" gutterBottom fontWeight="600" sx={{ mb: 4 }}>
                  Recent Analyses
                </Typography>
                
                {loading ? (
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', py: 6 }}>
                    <Loader className="animate-spin" size={32} color="#1976d2" />
                    <Typography variant="body1" sx={{ ml: 2 }} color="text.secondary">
                      Loading...
                    </Typography>
                  </Box>
                ) : recentAnalyses.length > 0 ? (
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    {recentAnalyses.map((analysis) => (
                      <Paper
                        key={analysis.request_id}
                        component={Link}
                        to={`/results/${analysis.request_id}`}
                        sx={{
                          border: '1px solid #e0e0e0',
                          borderRadius: 2,
                          p: { xs: 2, md: 3 },
                          textDecoration: 'none',
                          transition: 'all 0.2s',
                          backgroundColor: '#fafafa',
                          '&:hover': {
                            backgroundColor: 'white',
                            boxShadow: 3,
                            borderColor: 'primary.main'
                          }
                        }}
                      >
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            <Paper sx={{ 
                              p: 1, 
                              borderRadius: 1, 
                              backgroundColor: analysis.status === 'completed' ? 'success.50' : 'warning.50',
                              display: 'flex',
                              alignItems: 'center'
                            }}>
                              {getStatusIcon(analysis.status)}
                            </Paper>
                            <Box>
                              <Typography variant="h6" component="h4" fontWeight="600" sx={{ mb: 0.5 }}>
                                {analysis.client_company}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                {analysis.industry}
                              </Typography>
                            </Box>
                          </Box>
                          <Box sx={{ textAlign: 'right', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 1 }}>
                            <Typography variant="caption" color="text.secondary" fontWeight="500">
                              {formatDate(analysis.created_at)}
                            </Typography>
                            <Chip 
                              label={analysis.status.replace('_', ' ')}
                              size="small"
                              color={analysis.status === 'completed' ? 'success' : 'warning'}
                              sx={{ textTransform: 'capitalize', fontWeight: 500 }}
                            />
                            <ChevronRight size={16} color="#1976d2" />
                          </Box>
                        </Box>
                      </Paper>
                    ))}
                    
                    <Button
                      component={Link}
                      to="/reports"
                      variant="outlined"
                      fullWidth
                      sx={{ mt: 2, textTransform: 'none', fontWeight: 600 }}
                    >
                      View All Reports
                    </Button>
                  </Box>
                ) : (
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <FileText size={48} color="#9e9e9e" style={{ marginBottom: 16 }} />
                    <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                      No analyses yet. Start your first competitive analysis!
                    </Typography>
                    <Button
                      component={Link}
                      to="/analysis"
                      variant="contained"
                      sx={{ textTransform: 'none', fontWeight: 600 }}
                    >
                      Create Analysis
                    </Button>
                  </Box>
                )}
              </CardContent>
            </Card>
        </Box>

        {/* Quick Actions */}
        <Card sx={{ borderRadius: 2, boxShadow: 3, textAlign: 'center', maxWidth: '800px', mx: 'auto' }}>
          <CardContent sx={{ p: { xs: 4, md: 6 } }}>
            <Typography variant="h3" component="h2" gutterBottom fontWeight="600" sx={{ mb: 3 }}>
              Ready to Get Started?
            </Typography>
            <Typography variant="h6" color="text.secondary" sx={{ mb: 4, maxWidth: '600px', mx: 'auto' }}>
              Gain competitive advantage with AI-powered market intelligence
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'center', gap: 3, flexWrap: 'wrap' }}>
              <Button
                component={Link}
                to="/analysis"
                variant="contained"
                size="large"
                sx={{ 
                  fontSize: '1.125rem',
                  px: 4,
                  py: 2,
                  textTransform: 'none',
                  fontWeight: 600,
                  borderRadius: 2
                }}
              >
                Start Analysis
              </Button>
              <Button
                component={Link}
                to="/reports"
                variant="outlined"
                size="large"
                sx={{ 
                  fontSize: '1.125rem',
                  px: 4,
                  py: 2,
                  textTransform: 'none',
                  fontWeight: 600,
                  borderRadius: 2
                }}
              >
                Browse Reports
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Container>
    </Box>
  );
};

export default HomePage;