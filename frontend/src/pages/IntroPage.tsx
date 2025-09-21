import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Search, 
  TrendingUp, 
  Users, 
  Shield,
  BarChart3,
  Brain,
  Target,
  Zap,
  Eye,
  ArrowRight,
  CheckCircle,
  PlayCircle,
  Globe,
  Database,
  Cpu,
  LayoutDashboard
} from 'lucide-react';
import {
  Box,
  Container,
  Typography,
  Button,
  Paper,
  Card,
  CardContent,
  useTheme,
  alpha
} from '@mui/material';

const IntroPage: React.FC = () => {
  const theme = useTheme();
  const [animationStep, setAnimationStep] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setAnimationStep((prev) => (prev + 1) % 4);
    }, 2000);
    return () => clearInterval(timer);
  }, []);

  const agentFlow = [
    { icon: Search, label: "Discovery", color: "#2196f3", description: "Find competitors" },
    { icon: Database, label: "Collection", color: "#4caf50", description: "Gather data" },
    { icon: Brain, label: "Analysis", color: "#ff9800", description: "AI insights" },
    { icon: BarChart3, label: "Reports", color: "#9c27b0", description: "Generate reports" }
  ];

  const features = [
    {
      icon: Users,
      title: "Multi-Agent Intelligence",
      description: "Specialized AI agents working in orchestrated workflows",
      color: "#2196f3"
    },
    {
      icon: Globe,
      title: "Web Intelligence",
      description: "Real-time data collection from multiple sources",
      color: "#4caf50"
    },
    {
      icon: Shield,
      title: "Quality Assurance",
      description: "Advanced validation ensures accurate insights",
      color: "#ff9800"
    },
    {
      icon: Target,
      title: "Strategic Insights",
      description: "SWOT analysis and market positioning intelligence",
      color: "#9c27b0"
    }
  ];

  const stats = [
    { number: "4", label: "AI Agents", icon: Cpu },
    { number: "10+", label: "Data Sources", icon: Database },
    { number: "95%", label: "Accuracy Rate", icon: Target },
    { number: "< 5min", label: "Analysis Time", icon: Zap }
  ];

  return (
    <Box sx={{ 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      overflow: 'hidden',
      position: 'relative'
    }}>
      {/* Animated Background Elements */}
      <Box sx={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        opacity: 0.1,
        backgroundImage: `
          radial-gradient(circle at 20% 20%, rgba(255,255,255,0.3) 0%, transparent 50%),
          radial-gradient(circle at 80% 80%, rgba(255,255,255,0.2) 0%, transparent 50%),
          radial-gradient(circle at 40% 60%, rgba(255,255,255,0.1) 0%, transparent 50%)
        `
      }} />

      <Container maxWidth="xl" sx={{ position: 'relative', py: { xs: 4, md: 8 } }}>
        {/* Hero Section */}
        <Box sx={{ 
          textAlign: 'center', 
          mb: { xs: 8, md: 12 },
          pt: { xs: 6, md: 8 }
        }}>
          {/* Main Logo/Icon */}
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'center', 
            mb: 4,
            position: 'relative'
          }}>
            <Paper sx={{
              width: { xs: 120, md: 150 },
              height: { xs: 120, md: 150 },
              borderRadius: '50%',
              background: 'linear-gradient(45deg, #2196f3 30%, #21cbf3 90%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 20px 40px rgba(33, 150, 243, 0.3)',
              animation: 'pulse 2s infinite',
              '@keyframes pulse': {
                '0%': { transform: 'scale(1)', boxShadow: '0 20px 40px rgba(33, 150, 243, 0.3)' },
                '50%': { transform: 'scale(1.05)', boxShadow: '0 25px 50px rgba(33, 150, 243, 0.4)' },
                '100%': { transform: 'scale(1)', boxShadow: '0 20px 40px rgba(33, 150, 243, 0.3)' }
              }
            }}>
              <Brain size={60} color="white" />
            </Paper>
            
            {/* Orbiting Elements */}
            {[Search, BarChart3, Shield, Target].map((Icon, index) => (
              <Paper
                key={index}
                sx={{
                  position: 'absolute',
                  width: 40,
                  height: 40,
                  borderRadius: '50%',
                  backgroundColor: 'white',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: 3,
                  animation: `orbit${index} 8s linear infinite`,
                  [`@keyframes orbit${index}`]: {
                    '0%': { 
                      transform: `rotate(${index * 90}deg) translateX(100px) rotate(-${index * 90}deg)` 
                    },
                    '100%': { 
                      transform: `rotate(${360 + index * 90}deg) translateX(100px) rotate(-${360 + index * 90}deg)` 
                    }
                  }
                }}
              >
                <Icon size={20} color="#1976d2" />
              </Paper>
            ))}
          </Box>

          <Typography 
            variant="h1" 
            component="h1" 
            gutterBottom 
            fontWeight="bold"
            sx={{ 
              color: 'white', 
              mb: 3,
              fontSize: { xs: '2.5rem', md: '4rem' },
              textShadow: '0 4px 8px rgba(0,0,0,0.3)',
              background: 'linear-gradient(45deg, #ffffff 30%, #e3f2fd 90%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}
          >
            AI Competitive Intelligence
          </Typography>
          
          <Typography 
            variant="h4" 
            component="p" 
            sx={{ 
              color: 'rgba(255, 255, 255, 0.9)', 
              mb: 6, 
              maxWidth: '900px', 
              mx: 'auto',
              fontWeight: 300,
              lineHeight: 1.4
            }}
          >
            Harness the power of multi-agent AI workflows to discover, analyze, and outmaneuver your competition
          </Typography>

          {/* CTA Buttons */}
          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 3, flexWrap: 'wrap' }}>
            <Button
              component={Link}
              to="/analysis"
              variant="contained"
              size="large"
              startIcon={<PlayCircle size={24} />}
              endIcon={<ArrowRight size={20} />}
              sx={{ 
                fontSize: '1.25rem',
                px: 5,
                py: 2.5,
                borderRadius: 3,
                textTransform: 'none',
                fontWeight: 600,
                backgroundColor: 'white',
                color: 'primary.main',
                boxShadow: '0 8px 25px rgba(0,0,0,0.2)',
                '&:hover': {
                  backgroundColor: 'grey.100',
                  transform: 'translateY(-2px)',
                  boxShadow: '0 12px 35px rgba(0,0,0,0.3)'
                },
                transition: 'all 0.3s ease'
              }}
            >
              Start Analysis
            </Button>
            
            <Button
              component={Link}
              to="/home"
              variant="outlined"
              size="large"
              startIcon={<LayoutDashboard size={24} />}
              sx={{ 
                fontSize: '1.25rem',
                px: 5,
                py: 2.5,
                borderRadius: 3,
                textTransform: 'none',
                fontWeight: 600,
                color: 'white',
                borderColor: 'rgba(255, 255, 255, 0.5)',
                '&:hover': {
                  borderColor: 'white',
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  transform: 'translateY(-2px)'
                },
                transition: 'all 0.3s ease'
              }}
            >
              Dashboard
            </Button>
            
            <Button
              component={Link}
              to="/reports"
              variant="outlined"
              size="large"
              startIcon={<Eye size={24} />}
              sx={{ 
                fontSize: '1.25rem',
                px: 4,
                py: 2.5,
                borderRadius: 3,
                textTransform: 'none',
                fontWeight: 600,
                color: 'white',
                borderColor: 'rgba(255, 255, 255, 0.5)',
                '&:hover': {
                  borderColor: 'white',
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  transform: 'translateY(-2px)'
                },
                transition: 'all 0.3s ease'
              }}
            >
              View Demo
            </Button>
          </Box>
        </Box>

        {/* Agent Workflow Visualization */}
        <Box sx={{ mb: { xs: 8, md: 12 } }}>
          <Typography 
            variant="h3" 
            component="h2" 
            textAlign="center"
            fontWeight="bold"
            sx={{ color: 'white', mb: 6 }}
          >
            How Our AI Agents Work
          </Typography>
          
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: { xs: 2, md: 4 },
            maxWidth: '1000px',
            mx: 'auto'
          }}>
            {agentFlow.map((agent, index) => {
              const Icon = agent.icon;
              const isActive = animationStep === index;
              
              return (
                <React.Fragment key={index}>
                  <Box sx={{ 
                    textAlign: 'center',
                    transition: 'all 0.5s ease',
                    transform: isActive ? 'scale(1.1)' : 'scale(1)',
                    filter: isActive ? 'brightness(1.2)' : 'brightness(1)'
                  }}>
                    <Paper sx={{
                      width: { xs: 80, md: 100 },
                      height: { xs: 80, md: 100 },
                      borderRadius: '50%',
                      backgroundColor: agent.color,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      mb: 2,
                      mx: 'auto',
                      boxShadow: isActive ? `0 0 30px ${alpha(agent.color, 0.6)}` : '0 8px 25px rgba(0,0,0,0.2)',
                      transition: 'all 0.5s ease'
                    }}>
                      <Icon size={isActive ? 48 : 40} color="white" />
                    </Paper>
                    <Typography variant="h6" fontWeight="600" sx={{ color: 'white', mb: 1 }}>
                      {agent.label}
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                      {agent.description}
                    </Typography>
                  </Box>
                  
                  {index < agentFlow.length - 1 && (
                    <ArrowRight 
                      size={32} 
                      color="rgba(255, 255, 255, 0.7)" 
                      style={{ 
                        margin: '0 16px',
                        display: window.innerWidth < 768 ? 'none' : 'block'
                      }} 
                    />
                  )}
                </React.Fragment>
              );
            })}
          </Box>
        </Box>

        {/* Stats Section */}
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, 
          gap: 4, 
          mb: { xs: 8, md: 12 },
          maxWidth: '1000px',
          mx: 'auto'
        }}>
          {stats.map((stat, index) => {
            const Icon = stat.icon;
            return (
              <Card 
                key={index} 
                sx={{ 
                  borderRadius: 3, 
                  boxShadow: '0 10px 30px rgba(0,0,0,0.2)',
                  background: 'rgba(255, 255, 255, 0.95)',
                  backdropFilter: 'blur(10px)',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-5px)',
                    boxShadow: '0 15px 40px rgba(0,0,0,0.3)'
                  }
                }}
              >
                <CardContent sx={{ p: 3, textAlign: 'center' }}>
                  <Paper sx={{
                    width: 48,
                    height: 48,
                    borderRadius: '50%',
                    backgroundColor: 'primary.main',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mx: 'auto',
                    mb: 2
                  }}>
                    <Icon size={24} color="white" />
                  </Paper>
                  <Typography variant="h3" component="div" sx={{ 
                    color: 'primary.main', 
                    fontWeight: 700, 
                    mb: 1,
                    background: 'linear-gradient(45deg, #1976d2 30%, #2196f3 90%)',
                    backgroundClip: 'text',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent'
                  }}>
                    {stat.number}
                  </Typography>
                  <Typography variant="body1" color="text.secondary" fontWeight="500">
                    {stat.label}
                  </Typography>
                </CardContent>
              </Card>
            );
          })}
        </Box>

        {/* Features Grid */}
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, 
          gap: 4, 
          mb: { xs: 8, md: 12 } 
        }}>
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <Card 
                key={index}
                sx={{ 
                  borderRadius: 3, 
                  boxShadow: '0 10px 30px rgba(0,0,0,0.2)',
                  background: 'rgba(255, 255, 255, 0.95)',
                  backdropFilter: 'blur(10px)',
                  height: '100%',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-5px)',
                    boxShadow: '0 15px 40px rgba(0,0,0,0.3)'
                  }
                }}
              >
                <CardContent sx={{ p: 4, height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                    <Paper sx={{
                      width: 56,
                      height: 56,
                      borderRadius: 2,
                      backgroundColor: alpha(feature.color, 0.1),
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      mr: 3
                    }}>
                      <Icon size={28} color={feature.color} />
                    </Paper>
                    <Typography variant="h5" component="h3" fontWeight="600">
                      {feature.title}
                    </Typography>
                  </Box>
                  <Typography variant="body1" color="text.secondary" sx={{ flex: 1, lineHeight: 1.6 }}>
                    {feature.description}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', mt: 3 }}>
                    <CheckCircle size={20} color={feature.color} />
                    <Typography variant="body2" color={feature.color} fontWeight="600" sx={{ ml: 1 }}>
                      Enterprise Ready
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            );
          })}
        </Box>

        {/* Final CTA Section */}
        <Card sx={{ 
          borderRadius: 3, 
          boxShadow: '0 20px 50px rgba(0,0,0,0.3)',
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          textAlign: 'center',
          maxWidth: '800px',
          mx: 'auto'
        }}>
          <CardContent sx={{ p: { xs: 6, md: 8 } }}>
            <Typography variant="h3" component="h2" gutterBottom fontWeight="600" sx={{ 
              mb: 3,
              background: 'linear-gradient(45deg, #1976d2 30%, #2196f3 90%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              Ready to Dominate Your Market?
            </Typography>
            <Typography variant="h6" color="text.secondary" sx={{ mb: 4, maxWidth: '600px', mx: 'auto', lineHeight: 1.5 }}>
              Join the next generation of businesses using AI-powered competitive intelligence
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'center', gap: 3, flexWrap: 'wrap' }}>
              <Button
                component={Link}
                to="/analysis"
                variant="contained"
                size="large"
                startIcon={<TrendingUp size={24} />}
                endIcon={<ArrowRight size={20} />}
                sx={{ 
                  fontSize: '1.25rem',
                  px: 6,
                  py: 3,
                  borderRadius: 3,
                  textTransform: 'none',
                  fontWeight: 600,
                  background: 'linear-gradient(45deg, #1976d2 30%, #2196f3 90%)',
                  boxShadow: '0 8px 25px rgba(25, 118, 210, 0.4)',
                  '&:hover': {
                    boxShadow: '0 12px 35px rgba(25, 118, 210, 0.6)',
                    transform: 'translateY(-2px)'
                  },
                  transition: 'all 0.3s ease'
                }}
              >
                Start Your Analysis Now
              </Button>
              
              <Button
                component={Link}
                to="/home"
                variant="outlined"
                size="large"
                startIcon={<LayoutDashboard size={24} />}
                sx={{ 
                  fontSize: '1.25rem',
                  px: 6,
                  py: 3,
                  borderRadius: 3,
                  textTransform: 'none',
                  fontWeight: 600,
                  borderColor: 'primary.main',
                  color: 'primary.main',
                  '&:hover': {
                    backgroundColor: 'primary.50',
                    transform: 'translateY(-2px)',
                    borderColor: 'primary.dark'
                  },
                  transition: 'all 0.3s ease'
                }}
              >
                Go to Dashboard
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Container>
    </Box>
  );
};

export default IntroPage;