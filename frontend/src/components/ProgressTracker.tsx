import React from 'react';
import { 
  CheckCircle, 
  Clock, 
  Search, 
  Brain, 
  Shield, 
  FileText,
  AlertCircle,
  Loader
} from 'lucide-react';

interface ProgressStep {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<any>;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress?: number;
  message?: string;
  data?: any;
}

interface ProgressTrackerProps {
  currentStage: string;
  completedStages: string[];
  progress: number;
  status: string;
  message?: string;
  collectedData?: any;
}

const ProgressTracker: React.FC<ProgressTrackerProps> = ({
  currentStage,
  completedStages,
  progress,
  status,
  message,
  collectedData
}) => {
  // Define steps based on new 4-agent architecture
  const steps: ProgressStep[] = [
    {
      id: 'search',
      name: 'Search & Discovery',
      description: 'Finding competitors and collecting market data',
      icon: Search,
      status: getStepStatus('search', currentStage, completedStages, status)
    },
    {
      id: 'analysis',
      name: 'AI Analysis',
      description: 'Analyzing market landscape and competitive positioning',
      icon: Brain,
      status: getStepStatus('analysis', currentStage, completedStages, status)
    },
    {
      id: 'quality',
      name: 'Quality Assurance',
      description: 'Validating data quality and enriching competitor profiles',
      icon: Shield,
      status: getStepStatus('quality', currentStage, completedStages, status)
    },
    {
      id: 'report',
      name: 'Report Generation',
      description: 'Compiling final analysis and recommendations',
      icon: FileText,
      status: getStepStatus('report', currentStage, completedStages, status)
    }
  ];

  function getStepStatus(stepId: string, current: string, completed: string[], overallStatus: string): 'pending' | 'in_progress' | 'completed' | 'failed' {
    if (overallStatus === 'failed' && stepId === current) {
      return 'failed';
    }
    if (completed.includes(stepId)) {
      return 'completed';
    }
    if (stepId === current) {
      return 'in_progress';
    }
    return 'pending';
  }

  const getStepIcon = (step: ProgressStep) => {
    const IconComponent = step.icon;
    
    switch (step.status) {
      case 'completed':
        return <CheckCircle className="w-6 h-6 text-green-500" />;
      case 'in_progress':
        return <Loader className="w-6 h-6 text-blue-500 animate-spin" />;
      case 'failed':
        return <AlertCircle className="w-6 h-6 text-red-500" />;
      default:
        return <Clock className="w-6 h-6 text-gray-400" />;
    }
  };

  const getStepStyle = (step: ProgressStep) => {
    switch (step.status) {
      case 'completed':
        return 'border-green-500 bg-green-50';
      case 'in_progress':
        return 'border-blue-500 bg-blue-50';
      case 'failed':
        return 'border-red-500 bg-red-50';
      default:
        return 'border-gray-300 bg-gray-50';
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-6">
      {/* Overall Progress */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-2">
          <h2 className="text-xl font-semibold text-gray-800">Analysis Progress</h2>
          <span className="text-sm font-medium text-gray-600">{progress}% Complete</span>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div 
            className={`h-3 rounded-full transition-all duration-500 ${
              status === 'failed' ? 'bg-red-500' : 
              status === 'completed' ? 'bg-green-500' : 'bg-blue-500'
            }`}
            style={{ width: `${progress}%` }}
          ></div>
        </div>
        
        {message && (
          <p className="text-sm text-gray-600 mt-2">{message}</p>
        )}
      </div>

      {/* Step-by-Step Progress */}
      <div className="space-y-4">
        {steps.map((step, index) => (
          <div
            key={step.id}
            className={`border-2 rounded-lg p-4 transition-all duration-300 ${getStepStyle(step)}`}
          >
            <div className="flex items-start space-x-4">
              {/* Step Icon */}
              <div className="flex-shrink-0 mt-1">
                {getStepIcon(step)}
              </div>
              
              {/* Step Content */}
              <div className="flex-grow">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium text-gray-800">{step.name}</h3>
                  <span className="text-xs text-gray-500 capitalize">
                    {step.status.replace('_', ' ')}
                  </span>
                </div>
                
                <p className="text-sm text-gray-600 mt-1">{step.description}</p>
                
                {/* Show collected data for completed steps */}
                {step.status === 'completed' && collectedData && (
                  <div className="mt-3 p-3 bg-white rounded border">
                    <CollectedDataSummary stepId={step.id} data={collectedData} />
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Next Steps */}
      {status === 'completed' && (
        <div className="mt-8 p-4 bg-green-50 border border-green-200 rounded-lg">
          <h3 className="font-medium text-green-800 mb-2">Analysis Complete!</h3>
          <p className="text-sm text-green-700">
            Your competitive analysis report is ready. You can now view the detailed results, 
            competitor profiles, and strategic recommendations.
          </p>
        </div>
      )}

      {status === 'failed' && (
        <div className="mt-8 p-4 bg-red-50 border border-red-200 rounded-lg">
          <h3 className="font-medium text-red-800 mb-2">Analysis Failed</h3>
          <p className="text-sm text-red-700">
            There was an issue completing your analysis. Please check the logs or try again.
          </p>
        </div>
      )}
    </div>
  );
};

const CollectedDataSummary: React.FC<{ stepId: string; data: any }> = ({ stepId, data }) => {
  switch (stepId) {
    case 'search':
      return (
        <div className="text-sm">
          <p className="font-medium text-gray-700 mb-1">Search Results:</p>
          <ul className="text-gray-600 space-y-1">
            {data.competitors && (
              <li>• {data.competitors.length} competitors discovered</li>
            )}
            {data.competitors && data.competitors.length > 0 && (
              <li>• Multiple data sources searched and analyzed</li>
            )}
            {data.competitors && (
              <li>• {data.competitors.reduce((total: number, comp: any) => {
                return total + (comp.key_products?.length || 0) + (comp.recent_news?.length || 0) + 1;
              }, 0)} data points collected</li>
            )}
          </ul>
        </div>
      );
    
    case 'analysis':
      return (
        <div className="text-sm">
          <p className="font-medium text-gray-700 mb-1">Analysis Results:</p>
          <ul className="text-gray-600 space-y-1">
            {data.market_analysis && (
              <li>• Market landscape analyzed</li>
            )}
            {data.competitive_landscape && (
              <li>• Competitive positioning assessed</li>
            )}
            {data.recommendations && (
              <li>• {data.recommendations.length} strategic recommendations generated</li>
            )}
          </ul>
        </div>
      );
    
    case 'quality':
      return (
        <div className="text-sm">
          <p className="font-medium text-gray-700 mb-1">Quality Assessment:</p>
          <ul className="text-gray-600 space-y-1">
            {data.competitors && (
              <li>• {data.competitors.length} competitor profiles validated</li>
            )}
            {data.competitors && data.competitors.length > 0 && (
              <li>• {Math.round((data.competitors.filter((comp: any) => comp.description && comp.website).length / data.competitors.length) * 100)}% average data completeness</li>
            )}
            {data.competitors && (
              <li>• {data.competitors.filter((comp: any) => comp.threat_level === 'High' || comp.market_position).length} high-quality profiles</li>
            )}
          </ul>
        </div>
      );
    
    case 'report':
      return (
        <div className="text-sm">
          <p className="font-medium text-gray-700 mb-1">Report Generated:</p>
          <ul className="text-gray-600 space-y-1">
            <li>• Executive summary created</li>
            <li>• Detailed competitor analysis included</li>
            <li>• Strategic recommendations finalized</li>
            <li>• Report ready for download</li>
          </ul>
        </div>
      );
    
    default:
      return null;
  }
};

export default ProgressTracker;