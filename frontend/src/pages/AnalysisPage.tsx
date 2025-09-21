import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  Search, 
  Building2, 
  Target, 
  Users, 
  FileText, 
  AlertCircle,
  CheckCircle,
  Loader,
  Package,
  Settings
} from 'lucide-react';
import {
  Switch,
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  Tab,
  Tabs,
  TextField,
  Select,
  MenuItem,
  FormControl,
  Alert,
  Paper,
  Checkbox,
  FormControlLabel
} from '@mui/material';
import { analysisAPI } from '../services/api';
import { startProductComparison } from '../services/api';
import AutocompleteInput from '../components/AutocompleteInput';
import AutocompleteTextarea from '../components/AutocompleteTextarea';
import { suggestionService } from '../services/suggestionService';
import { ProductComparisonRequest } from '../types';

interface AnalysisForm {
  client_company: string;
  industry: string;
  target_market: string;
  business_model: string;
  specific_requirements: string;
  max_competitors: number;
}

interface ProductForm {
  client_product: string;
  client_company: string;
  product_category: string;
  target_market: string;
  specific_requirements: string;
  max_products: number;
  include_indirect_competitors: boolean;
  comparison_criteria: string[];
}

const AnalysisPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [activeTab, setActiveTab] = useState<'company' | 'product'>('company');
  const [form, setForm] = useState<AnalysisForm>({
    client_company: '',
    industry: '',
    target_market: '',
    business_model: '',
    specific_requirements: '',
    max_competitors: 10
  });
  const [productForm, setProductForm] = useState<ProductForm>({
    client_product: '',
    client_company: '',
    product_category: '',
    target_market: '',
    specific_requirements: '',
    max_products: 10,
    include_indirect_competitors: true,
    comparison_criteria: ['features', 'pricing', 'performance', 'user_reviews']
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isRestart, setIsRestart] = useState(false);
  const [demoMode, setDemoMode] = useState<boolean>(true);
  const [demoModeLoading, setDemoModeLoading] = useState(false);

  // Check for pre-filled data from restart analysis
  useEffect(() => {
    if (location.state?.prefillData) {
      const prefillData = location.state.prefillData;
      
      // Check if this is a product analysis restart
      if (prefillData.analysisType === 'product') {
        // Switch to product tab and fill product form
        setActiveTab('product');
        setProductForm({
          client_product: prefillData.client_product || '',
          client_company: prefillData.client_company || '',
          product_category: prefillData.product_category || '',
          target_market: prefillData.target_market || '',
          specific_requirements: prefillData.specific_requirements || '',
          max_products: prefillData.max_products || 10,
          comparison_criteria: prefillData.comparison_criteria || [],
          include_indirect_competitors: false
        });
      } else {
        // Default to company tab and fill company form
        setActiveTab('company');
        setForm({
          client_company: prefillData.client_company || '',
          industry: prefillData.industry || '',
          target_market: prefillData.target_market || '',
          business_model: prefillData.business_model || '',
          specific_requirements: prefillData.specific_requirements || '',
          max_competitors: prefillData.max_competitors || 10
        });
      }
      
      setIsRestart(true);
      // Clear the location state after using it
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  // Load demo mode status on component mount
  useEffect(() => {
    const loadDemoModeStatus = async () => {
      try {
        const response = await analysisAPI.getDemoModeStatus();
        setDemoMode(response.data.demo_mode);
      } catch (err) {
        console.error('Failed to load demo mode status:', err);
        // Default to demo mode if we can't load status
        setDemoMode(true);
      }
    };
    
    loadDemoModeStatus();
  }, []);

  const toggleDemoMode = async () => {
    try {
      setDemoModeLoading(true);
      const response = await analysisAPI.toggleDemoMode();
      setDemoMode(response.data.current_demo_mode);
      
      // Show success message
      setSuccess(`Demo mode ${response.data.current_demo_mode ? 'enabled' : 'disabled'} - using ${response.data.current_demo_mode ? 'mock' : 'real'} data`);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      console.error('Failed to toggle demo mode:', err);
      setError('Failed to toggle demo mode. Please try again.');
      setTimeout(() => setError(null), 3000);
    } finally {
      setDemoModeLoading(false);
    }
  };

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setForm(prev => ({
      ...prev,
      [name]: name === 'max_competitors' ? parseInt(value) || 1 : value
    }));
  };

  const handleProductInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type, checked } = e.target as HTMLInputElement;
    setProductForm(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : (name === 'max_products' ? parseInt(value) || 1 : value)
    }));
  };

  const toggleCriterion = (criterion: string) => {
    setProductForm(prev => ({
      ...prev,
      comparison_criteria: prev.comparison_criteria.includes(criterion)
        ? prev.comparison_criteria.filter(c => c !== criterion)
        : [...prev.comparison_criteria, criterion]
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);

    try {
      // Validate form
      if (!form.client_company.trim()) {
        throw new Error('Client company name is required');
      }
      if (!form.industry.trim()) {
        throw new Error('Industry is required');
      }
      if (!form.target_market.trim()) {
        throw new Error('Target market is required');
      }
      if (!form.business_model.trim()) {
        throw new Error('Business model is required');
      }

      // Save form data to suggestions before submitting
      suggestionService.saveFormData(form);

      // Start analysis
      const response = await analysisAPI.startAnalysis(form);
      
      // Check if we have a proper request_id from the response
      if (response.data && response.data.request_id) {
        setSuccess('Analysis started successfully! Redirecting to progress tracking...');
        
        // Navigate to results page with the actual request_id immediately
        setTimeout(() => {
          navigate(`/results/${response.data.request_id}`);
        }, 1000);
      } else {
        throw new Error('Invalid response from server - no request ID received');
      }

    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to start analysis');
    } finally {
      setLoading(false);
    }
  };

  const handleProductSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);

    try {
      // Validate product form
      if (!productForm.client_product.trim()) {
        throw new Error('Product name is required');
      }
      if (!productForm.client_company.trim()) {
        throw new Error('Company name is required');
      }
      if (!productForm.product_category.trim()) {
        throw new Error('Product category is required');
      }
      if (!productForm.target_market.trim()) {
        throw new Error('Target market is required');
      }
      if (productForm.comparison_criteria.length === 0) {
        throw new Error('At least one comparison criterion must be selected');
      }

      // Save product form data to suggestions before submitting
      suggestionService.saveFormData(productForm);

      // Convert to ProductComparisonRequest format
      const productRequest: ProductComparisonRequest = {
        client_product: productForm.client_product,
        client_company: productForm.client_company,
        product_category: productForm.product_category,
        target_market: productForm.target_market,
        specific_requirements: productForm.specific_requirements,
        max_products: productForm.max_products,
        include_indirect_competitors: productForm.include_indirect_competitors,
        comparison_criteria: productForm.comparison_criteria
      };

      // Start product comparison
      const response = await startProductComparison(productRequest);
      
      if (response && response.request_id) {
        setSuccess('Product comparison started successfully! Redirecting to progress tracking...');
        
        // Navigate to results page
        setTimeout(() => {
          navigate(`/results/${response.request_id}`);
        }, 1000);
      } else {
        throw new Error('Invalid response from server - no request ID received');
      }

    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to start product comparison');
    } finally {
      setLoading(false);
    }
  };

  const industryOptions = [
    'Technology',
    'Healthcare',
    'Finance',
    'Education',
    'E-commerce',
    'Manufacturing',
    'Retail',
    'Real Estate',
    'Transportation',
    'Media & Entertainment',
    'Food & Beverage',
    'Energy',
    'Other'
  ];

  const businessModelOptions = [
    'B2B SaaS',
    'B2C SaaS',
    'E-commerce',
    'Marketplace',
    'Subscription',
    'Freemium',
    'Enterprise',
    'Consulting',
    'Product-based',
    'Service-based',
    'Other'
  ];

  const availableCriteria = [
    { value: 'features', label: 'Features & Capabilities' },
    { value: 'pricing', label: 'Pricing & Value' },
    { value: 'performance', label: 'Performance & Speed' },
    { value: 'user_reviews', label: 'User Reviews & Ratings' },
    { value: 'integrations', label: 'Integrations & API' },
    { value: 'support', label: 'Customer Support' },
    { value: 'security', label: 'Security & Compliance' },
    { value: 'scalability', label: 'Scalability' }
  ];

  return (
    <Box sx={{ 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      py: { xs: 4, md: 6 },
      px: { xs: 2, md: 3 }
    }}>
      <Container maxWidth="lg">
        <Box sx={{ textAlign: 'center', mb: { xs: 4, md: 6 } }}>
          <Typography 
            variant="h3" 
            component="h1" 
            gutterBottom 
            fontWeight="bold"
            sx={{ color: 'white', mb: 2 }}
          >
            {isRestart ? 'Restart Competitive Analysis' : 'Start New Competitive Analysis'}
          </Typography>
          <Typography 
            variant="h6" 
            sx={{ color: 'rgba(255, 255, 255, 0.9)', maxWidth: '800px', mx: 'auto' }}
          >
            {isRestart 
              ? 'Review and modify the pre-filled information, then start a new analysis'
              : activeTab === 'company' 
                ? 'Provide details about your company and we\'ll analyze your competitive landscape'
                : 'Compare your product against competitors with detailed feature and performance analysis'}
          </Typography>
        </Box>

        {/* Tab Navigation */}
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 4 }}>
          <Card sx={{ borderRadius: 2, boxShadow: 3 }}>
            <Tabs 
              value={activeTab} 
              onChange={(_, newValue) => {
                setActiveTab(newValue);
                setError(null);
                setSuccess(null);
              }}
              sx={{ 
                '& .MuiTab-root': {
                  textTransform: 'none',
                  fontWeight: 600,
                  fontSize: '1rem',
                  minWidth: 160
                }
              }}
            >
              <Tab 
                icon={<Building2 size={20} />} 
                iconPosition="start"
                label="Company Analysis" 
                value="company"
              />
              <Tab 
                icon={<Package size={20} />} 
                iconPosition="start"
                label="Product Comparison" 
                value="product"
              />
            </Tabs>
          </Card>
        </Box>

      
      {isRestart && (
        <Alert 
          severity="info" 
          icon={<AlertCircle size={20} />}
          sx={{ 
            mb: 4, 
            borderRadius: 2,
            backgroundColor: '#e3f2fd',
            border: '1px solid #2196f3',
            '& .MuiAlert-message': {
              fontSize: '0.95rem',
              fontWeight: 500
            }
          }}
        >
          This form has been pre-filled with data from your previous analysis. Review and modify as needed.
        </Alert>
      )}

        <Card sx={{ borderRadius: 2, boxShadow: 3 }}>
          <CardContent sx={{ p: { xs: 3, md: 4 } }}>
        {/* Company Analysis Tab */}
        {activeTab === 'company' && (
          <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          
          {/* Demo Mode Toggle - Company Form */}
          <Paper sx={{ 
            p: 3, 
            backgroundColor: '#f5f5f5', 
            border: '1px solid #e0e0e0',
            borderRadius: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="body1" fontWeight="500" color="text.primary">
                Data Source:
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {demoMode ? 'Demo data' : 'Live data'}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="body2" color="text.secondary">Demo</Typography>
              <Switch
                checked={!demoMode}
                onChange={toggleDemoMode}
                disabled={demoModeLoading}
                color="success"
                size="medium"
              />
              <Typography variant="body2" color="text.secondary">Live</Typography>
            </Box>
          </Paper>
          
          {/* Alert Messages */}
          {error && (
            <Alert 
              severity="error" 
              icon={<AlertCircle size={20} />}
              sx={{ borderRadius: 2 }}
            >
              {error}
            </Alert>
          )}

          {success && (
            <Alert 
              severity="success" 
              icon={<CheckCircle size={20} />}
              sx={{ borderRadius: 2 }}
            >
              {success}
            </Alert>
          )}

          {/* Company Information */}
          <Box sx={{ 
            display: 'grid', 
            gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, 
            gap: 4 
          }}>
            <Box>
              <Typography variant="subtitle1" fontWeight="600" sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 1.5, 
                mb: 2,
                color: 'text.primary'
              }}>
                <Building2 size={18} />
                Client Company Name *
              </Typography>
              <Box sx={{ '& .MuiInputBase-root': { borderRadius: 2 } }}>
                <AutocompleteInput
                  name="client_company"
                  value={form.client_company}
                  onChange={(value) => setForm(prev => ({ ...prev, client_company: value }))}
                  placeholder="Enter your company name"
                  required
                />
              </Box>
            </Box>

            <Box>
              <Typography variant="subtitle1" fontWeight="600" sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 1.5, 
                mb: 2,
                color: 'text.primary'
              }}>
                <Target size={18} />
                Industry *
              </Typography>
              <FormControl fullWidth required>
                <Select
                  name="industry"
                  value={form.industry}
                  onChange={(e) => handleInputChange(e as any)}
                  displayEmpty
                  sx={{ borderRadius: 2 }}
                >
                  <MenuItem value="">
                    <Typography variant="body2" color="text.secondary">Select your industry</Typography>
                  </MenuItem>
                  {industryOptions.map(industry => (
                    <MenuItem key={industry} value={industry}>
                      {industry}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
          </Box>

          <Box sx={{ 
            display: 'grid', 
            gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, 
            gap: 4 
          }}>
            <Box>
              <Typography variant="subtitle1" fontWeight="600" sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 1.5, 
                mb: 2,
                color: 'text.primary'
              }}>
                <Users size={18} />
                Target Market *
              </Typography>
              <Box sx={{ '& .MuiInputBase-root': { borderRadius: 2 } }}>
                <AutocompleteInput
                  name="target_market"
                  value={form.target_market}
                  onChange={(value) => setForm(prev => ({ ...prev, target_market: value }))}
                  placeholder="e.g., North America, SMBs, Enterprise"
                  required
                />
              </Box>
            </Box>

            <Box>
              <Typography variant="subtitle1" fontWeight="600" sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 1.5, 
                mb: 2,
                color: 'text.primary'
              }}>
                <Building2 size={18} />
                Business Model *
              </Typography>
              <FormControl fullWidth required>
                <Select
                  name="business_model"
                  value={form.business_model}
                  onChange={(e) => handleInputChange(e as any)}
                  displayEmpty
                  sx={{ borderRadius: 2 }}
                >
                  <MenuItem value="">
                    <Typography variant="body2" color="text.secondary">Select business model</Typography>
                  </MenuItem>
                  {businessModelOptions.map(model => (
                    <MenuItem key={model} value={model}>
                      {model}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
          </Box>

          {/* Analysis Parameters */}
          <Box>
            <Typography variant="subtitle1" fontWeight="600" sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: 1.5, 
              mb: 2,
              color: 'text.primary'
            }}>
              <Users size={18} />
              Maximum Competitors to Analyze
            </Typography>
            <TextField
              type="number"
              name="max_competitors"
              value={form.max_competitors}
              onChange={handleInputChange}
              fullWidth
              inputProps={{ min: 1, max: 50 }}
              placeholder="10"
              sx={{ 
                '& .MuiOutlinedInput-root': { 
                  borderRadius: 2,
                  maxWidth: 200
                }
              }}
            />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1.5 }}>
              Recommended: 10-20 competitors for comprehensive analysis
            </Typography>
          </Box>

          {/* Specific Requirements */}
          <Box>
            <Typography variant="subtitle1" fontWeight="600" sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: 1.5, 
              mb: 2,
              color: 'text.primary'
            }}>
              <FileText size={18} />
              Specific Requirements (Optional)
            </Typography>
            <Box sx={{ '& .MuiInputBase-root': { borderRadius: 2 } }}>
              <AutocompleteTextarea
                name="specific_requirements"
                value={form.specific_requirements}
                onChange={(value) => setForm(prev => ({ ...prev, specific_requirements: value }))}
                placeholder="Any specific focus areas, competitor types, or analysis requirements..."
                rows={4}
              />
            </Box>
          </Box>

          {/* Analysis Preview */}
          <Paper sx={{ 
            p: 4, 
            backgroundColor: '#f5f5f5', 
            border: '1px solid #e0e0e0',
            borderRadius: 2
          }}>
            <Typography variant="h6" fontWeight="600" color="text.primary" sx={{ mb: 3 }}>
              Analysis Preview
            </Typography>
            <Box sx={{ 
              display: 'grid', 
              gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, 
              gap: 3 
            }}>
              <Box>
                <Typography variant="body2" color="text.secondary">Company:</Typography>
                <Typography variant="body1" fontWeight="500" sx={{ ml: 2 }}>
                  {form.client_company || 'Not specified'}
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary">Industry:</Typography>
                <Typography variant="body1" fontWeight="500" sx={{ ml: 2 }}>
                  {form.industry || 'Not specified'}
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary">Target Market:</Typography>
                <Typography variant="body1" fontWeight="500" sx={{ ml: 2 }}>
                  {form.target_market || 'Not specified'}
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary">Max Competitors:</Typography>
                <Typography variant="body1" fontWeight="500" sx={{ ml: 2 }}>
                  {form.max_competitors}
                </Typography>
              </Box>
            </Box>
          </Paper>

          {/* Analysis Information */}
          <Paper sx={{ 
            p: 4, 
            backgroundColor: '#e3f2fd', 
            border: '1px solid #2196f3',
            borderRadius: 2
          }}>
            <Typography variant="h6" fontWeight="600" color="primary.main" sx={{ mb: 3 }}>
              What to Expect
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                <Box sx={{ 
                  width: 8, 
                  height: 8, 
                  backgroundColor: 'primary.main', 
                  borderRadius: '50%', 
                  mt: 1,
                  flexShrink: 0 
                }} />
                <Typography variant="body2" color="primary.dark">
                  <strong>Discovery:</strong> AI agents will identify competitors 
                  across multiple data sources
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                <Box sx={{ 
                  width: 8, 
                  height: 8, 
                  backgroundColor: 'primary.main', 
                  borderRadius: '50%', 
                  mt: 1,
                  flexShrink: 0 
                }} />
                <Typography variant="body2" color="primary.dark">
                  <strong>Analysis:</strong> Comprehensive market and competitive 
                  landscape analysis
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                <Box sx={{ 
                  width: 8, 
                  height: 8, 
                  backgroundColor: 'primary.main', 
                  borderRadius: '50%', 
                  mt: 1,
                  flexShrink: 0 
                }} />
                <Typography variant="body2" color="primary.dark">
                  <strong>Insights:</strong> Strategic recommendations and 
                  competitive positioning
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                <Box sx={{ 
                  width: 8, 
                  height: 8, 
                  backgroundColor: 'primary.main', 
                  borderRadius: '50%', 
                  mt: 1,
                  flexShrink: 0 
                }} />
                <Typography variant="body2" color="primary.dark">
                  <strong>Duration:</strong> Typically completes within 15-30 minutes
                </Typography>
              </Box>
            </Box>
          </Paper>

          {/* Submit Buttons */}
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pt: 3 }}>
            <Button
              type="button"
              onClick={() => navigate('/')}
              variant="outlined"
              disabled={loading}
              sx={{ 
                textTransform: 'none', 
                fontWeight: 600,
                px: 4,
                py: 1.5,
                borderRadius: 2
              }}
            >
              Cancel
            </Button>
            
            <Button
              type="submit"
              variant="contained"
              disabled={loading}
              startIcon={loading ? <Loader className="animate-spin" size={20} /> : <Search size={20} />}
              sx={{ 
                textTransform: 'none', 
                fontWeight: 600,
                px: 5,
                py: 1.5,
                borderRadius: 2,
                fontSize: '1rem'
              }}
            >
              {loading ? 'Starting Analysis...' : 'Start Analysis'}
            </Button>
          </Box>
        </Box>
        )}

        {/* Product Comparison Tab */}
        {activeTab === 'product' && (
          <Box component="form" onSubmit={handleProductSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            
            {/* Demo Mode Toggle - Product Form */}
            <Paper sx={{ 
              p: 3, 
              backgroundColor: '#f5f5f5', 
              border: '1px solid #e0e0e0',
              borderRadius: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Typography variant="body1" fontWeight="500" color="text.primary">
                  Data Source:
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {demoMode ? 'Demo data' : 'Live data'}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Typography variant="body2" color="text.secondary">Demo</Typography>
                <Switch
                  checked={!demoMode}
                  onChange={toggleDemoMode}
                  disabled={demoModeLoading}
                  color="success"
                  size="medium"
                />
                <Typography variant="body2" color="text.secondary">Live</Typography>
              </Box>
            </Paper>
            
            {/* Alert Messages */}
            {error && (
              <Alert 
                severity="error" 
                icon={<AlertCircle size={20} />}
                sx={{ borderRadius: 2 }}
              >
                {error}
              </Alert>
            )}

            {success && (
              <Alert 
                severity="success" 
                icon={<CheckCircle size={20} />}
                sx={{ borderRadius: 2 }}
              >
                {success}
              </Alert>
            )}

            {/* Product Information */}
            <Box sx={{ 
              display: 'grid', 
              gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, 
              gap: 4 
            }}>
              <Box>
                <Typography variant="subtitle1" fontWeight="600" sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 1.5, 
                  mb: 2,
                  color: 'text.primary'
                }}>
                  <Package size={18} />
                  Product Name *
                </Typography>
                <Box sx={{ '& .MuiInputBase-root': { borderRadius: 2 } }}>
                  <AutocompleteInput
                    name="client_product"
                    value={productForm.client_product}
                    onChange={(value) => setProductForm(prev => ({ ...prev, client_product: value }))}
                    placeholder="Enter your product name"
                    required
                  />
                </Box>
              </Box>

              <Box>
                <Typography variant="subtitle1" fontWeight="600" sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 1.5, 
                  mb: 2,
                  color: 'text.primary'
                }}>
                  <Building2 size={18} />
                  Company Name *
                </Typography>
                <Box sx={{ '& .MuiInputBase-root': { borderRadius: 2 } }}>
                  <AutocompleteInput
                    name="client_company"
                    value={productForm.client_company}
                    onChange={(value) => setProductForm(prev => ({ ...prev, client_company: value }))}
                    placeholder="Enter your company name"
                    required
                  />
                </Box>
              </Box>
            </Box>

            {/* Product Category and Target Market */}
            <Box sx={{ 
              display: 'grid', 
              gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, 
              gap: 4 
            }}>
              <Box>
                <Typography variant="subtitle1" fontWeight="600" sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 1.5, 
                  mb: 2,
                  color: 'text.primary'
                }}>
                  <Target size={18} />
                  Product Category *
                </Typography>
                <Box sx={{ '& .MuiInputBase-root': { borderRadius: 2 } }}>
                  <AutocompleteInput
                    name="product_category"
                    value={productForm.product_category}
                    onChange={(value) => setProductForm(prev => ({ ...prev, product_category: value }))}
                    placeholder="e.g., Project Management, CRM, Communication Tools"
                    required
                  />
                </Box>
              </Box>

              <Box>
                <Typography variant="subtitle1" fontWeight="600" sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 1.5, 
                  mb: 2,
                  color: 'text.primary'
                }}>
                  <Users size={18} />
                  Target Market *
                </Typography>
                <TextField
                  type="text"
                  name="target_market"
                  value={productForm.target_market}
                  onChange={handleProductInputChange}
                  fullWidth
                  placeholder="e.g., Small businesses, Enterprise, Developers"
                  required
                  sx={{ 
                    '& .MuiOutlinedInput-root': { 
                      borderRadius: 2
                    }
                  }}
                />
              </Box>
            </Box>

            {/* Comparison Criteria */}
            <Box>
              <Typography variant="subtitle1" fontWeight="600" sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 1.5, 
                mb: 3,
                color: 'text.primary'
              }}>
                <Settings size={18} />
                Comparison Criteria *
              </Typography>
              
              <Box sx={{ 
                display: 'grid', 
                gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, 
                gap: 2
              }}>
                {availableCriteria.map((criterion) => (
                  <Paper
                    key={criterion.value}
                    sx={{
                      p: 2,
                      border: '1px solid #e0e0e0',
                      borderRadius: 2,
                      backgroundColor: productForm.comparison_criteria.includes(criterion.value) ? '#e3f2fd' : 'white',
                      borderColor: productForm.comparison_criteria.includes(criterion.value) ? '#2196f3' : '#e0e0e0',
                      '&:hover': {
                        backgroundColor: productForm.comparison_criteria.includes(criterion.value) ? '#e3f2fd' : '#f5f5f5',
                        cursor: 'pointer'
                      },
                      transition: 'all 0.2s ease'
                    }}
                    onClick={() => toggleCriterion(criterion.value)}
                  >
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={productForm.comparison_criteria.includes(criterion.value)}
                          onChange={() => toggleCriterion(criterion.value)}
                          sx={{ 
                            color: 'primary.main',
                            '&.Mui-checked': {
                              color: 'primary.main',
                            }
                          }}
                        />
                      }
                      label={
                        <Typography variant="body2" fontWeight="500">
                          {criterion.label}
                        </Typography>
                      }
                      sx={{ 
                        margin: 0,
                        width: '100%',
                        '& .MuiFormControlLabel-label': {
                          fontSize: '0.875rem'
                        }
                      }}
                    />
                  </Paper>
                ))}
              </Box>
              
              {productForm.comparison_criteria.length === 0 && (
                <Typography variant="body2" color="error" sx={{ mt: 2 }}>
                  Please select at least one comparison criterion
                </Typography>
              )}
              
              <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
                Selected: {productForm.comparison_criteria.length} of {availableCriteria.length} criteria
              </Typography>
            </Box>

            {/* Additional Settings */}
            <Box sx={{ 
              display: 'grid', 
              gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, 
              gap: 4,
              alignItems: 'start'
            }}>
              <Box>
                <Typography variant="subtitle1" fontWeight="600" sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 1.5, 
                  mb: 2,
                  color: 'text.primary'
                }}>
                  <Target size={18} />
                  Maximum Products to Compare
                </Typography>
                <TextField
                  type="number"
                  name="max_products"
                  value={productForm.max_products}
                  onChange={handleProductInputChange}
                  fullWidth
                  inputProps={{ min: 1, max: 20 }}
                  placeholder="10"
                  sx={{ 
                    '& .MuiOutlinedInput-root': { 
                      borderRadius: 2,
                      maxWidth: 200
                    }
                  }}
                />
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1.5 }}>
                  Recommended: 5-15 products for comprehensive comparison
                </Typography>
              </Box>

              <Box sx={{ 
                display: 'flex', 
                alignItems: 'center',
                pt: { xs: 2, md: 6 }
              }}>
                <FormControlLabel
                  control={
                    <Checkbox
                      name="include_indirect_competitors"
                      checked={productForm.include_indirect_competitors}
                      onChange={handleProductInputChange}
                      sx={{ 
                        color: 'primary.main',
                        '&.Mui-checked': {
                          color: 'primary.main',
                        }
                      }}
                    />
                  }
                  label={
                    <Typography variant="body1" fontWeight="500">
                      Include Indirect Competitors
                    </Typography>
                  }
                  sx={{ margin: 0 }}
                />
              </Box>
            </Box>

            {/* Specific Requirements */}
            <Box>
              <Typography variant="subtitle1" fontWeight="600" sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 1.5, 
                mb: 2,
                color: 'text.primary'
              }}>
                <FileText size={18} />
                Specific Requirements (Optional)
              </Typography>
              <Box sx={{ '& .MuiInputBase-root': { borderRadius: 2 } }}>
                <AutocompleteTextarea
                  name="specific_requirements"
                  value={productForm.specific_requirements}
                  onChange={(value) => setProductForm(prev => ({ ...prev, specific_requirements: value }))}
                  placeholder="Additional requirements or focus areas for the comparison..."
                  rows={4}
                />
              </Box>
            </Box>

            {/* Comparison Preview */}
            <Paper sx={{ 
              p: 4, 
              backgroundColor: '#f5f5f5', 
              border: '1px solid #e0e0e0',
              borderRadius: 2
            }}>
              <Typography variant="h6" fontWeight="600" color="text.primary" sx={{ mb: 3 }}>
                Comparison Preview
              </Typography>
              <Box sx={{ 
                display: 'grid', 
                gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, 
                gap: 3 
              }}>
                <Box>
                  <Typography variant="body2" color="text.secondary">Product:</Typography>
                  <Typography variant="body1" fontWeight="500" sx={{ ml: 2 }}>
                    {productForm.client_product || 'Not specified'}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">Company:</Typography>
                  <Typography variant="body1" fontWeight="500" sx={{ ml: 2 }}>
                    {productForm.client_company || 'Not specified'}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">Category:</Typography>
                  <Typography variant="body1" fontWeight="500" sx={{ ml: 2 }}>
                    {productForm.product_category || 'Not specified'}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">Criteria Selected:</Typography>
                  <Typography variant="body1" fontWeight="500" sx={{ ml: 2 }}>
                    {productForm.comparison_criteria.length}
                  </Typography>
                </Box>
              </Box>
            </Paper>

            {/* What to Expect */}
            <Paper sx={{ 
              p: 4, 
              backgroundColor: '#e3f2fd', 
              border: '1px solid #2196f3',
              borderRadius: 2
            }}>
              <Typography variant="h6" fontWeight="600" color="primary.main" sx={{ mb: 3 }}>
                What to Expect
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                  <Box sx={{ 
                    width: 8, 
                    height: 8, 
                    backgroundColor: 'primary.main', 
                    borderRadius: '50%', 
                    mt: 1,
                    flexShrink: 0 
                  }} />
                  <Typography variant="body2" color="primary.dark">
                    <strong>Product Discovery:</strong> AI agents will identify competing products 
                    in your category
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                  <Box sx={{ 
                    width: 8, 
                    height: 8, 
                    backgroundColor: 'primary.main', 
                    borderRadius: '50%', 
                    mt: 1,
                    flexShrink: 0 
                  }} />
                  <Typography variant="body2" color="primary.dark">
                    <strong>Feature Analysis:</strong> Detailed comparison of features, 
                    pricing, and capabilities
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                  <Box sx={{ 
                    width: 8, 
                    height: 8, 
                    backgroundColor: 'primary.main', 
                    borderRadius: '50%', 
                    mt: 1,
                    flexShrink: 0 
                  }} />
                  <Typography variant="body2" color="primary.dark">
                    <strong>Performance Review:</strong> User reviews, ratings, and 
                    performance benchmarks
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                  <Box sx={{ 
                    width: 8, 
                    height: 8, 
                    backgroundColor: 'primary.main', 
                    borderRadius: '50%', 
                    mt: 1,
                    flexShrink: 0 
                  }} />
                  <Typography variant="body2" color="primary.dark">
                    <strong>Duration:</strong> Typically completes within 10-20 minutes
                  </Typography>
                </Box>
              </Box>
            </Paper>

            {/* Submit Buttons */}
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pt: 3 }}>
              <Button
                type="button"
                onClick={() => navigate('/')}
                variant="outlined"
                disabled={loading}
                sx={{ 
                  textTransform: 'none', 
                  fontWeight: 600,
                  px: 4,
                  py: 1.5,
                  borderRadius: 2
                }}
              >
                Cancel
              </Button>
              
              <Button
                type="submit"
                variant="contained"
                disabled={loading || productForm.comparison_criteria.length === 0}
                startIcon={loading ? <Loader className="animate-spin" size={20} /> : <Search size={20} />}
                sx={{ 
                  textTransform: 'none', 
                  fontWeight: 600,
                  px: 5,
                  py: 1.5,
                  borderRadius: 2,
                  fontSize: '1rem'
                }}
              >
                {loading ? 'Starting Comparison...' : 'Start Product Comparison'}
              </Button>
            </Box>
          </Box>
        )}
          </CardContent>
        </Card>
      </Container>
    </Box>
  );
};

export default AnalysisPage;