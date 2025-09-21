import React, { useState, useEffect } from 'react';
import { Search, Clock, AlertTriangle, CheckCircle, Eye, EyeOff, ChevronDown, ChevronUp } from 'lucide-react';
import { analysisAPI } from '../services/api';

interface SearchLog {
  timestamp: string;
  search_type: string;
  query: string;
  parameters: {
    max_results?: number;
    search_depth?: string;
    demo_mode?: boolean;
    include_domains?: string[];
    exclude_domains?: string[];
  };
  results_count: number;
  results: any[];
  processing_notes?: string;
  duration_ms?: number;
  error?: string;
}

interface SearchLogsProps {
  requestId: string;
}

const SearchLogs: React.FC<SearchLogsProps> = ({ requestId }) => {
  const [searchLogs, setSearchLogs] = useState<SearchLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showResults, setShowResults] = useState<{ [key: number]: boolean }>({});
  const [expandedLogs, setExpandedLogs] = useState<{ [key: number]: boolean }>({});

  useEffect(() => {
    loadSearchLogs();
  }, [requestId]);

  const loadSearchLogs = async () => {
    try {
      setLoading(true);
      const response = await analysisAPI.getSearchLogs(requestId);
      setSearchLogs(response.data.search_logs || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load search logs');
    } finally {
      setLoading(false);
    }
  };

  const toggleResults = (index: number) => {
    setShowResults(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const toggleExpanded = (index: number) => {
    setExpandedLogs(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const formatDuration = (ms?: number) => {
    if (!ms) return 'N/A';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const getSearchTypeIcon = (type: string) => {
    switch (type) {
      case 'competitor_search':
        return '🏢';
      case 'company_details':
        return '📋';
      case 'market_analysis':
        return '📊';
      case 'custom':
        return '🔍';
      default:
        return '📝';
    }
  };

  const getStatusColor = (log: SearchLog) => {
    if (log.error) return 'border-red-200 bg-red-50';
    if (log.results_count === 0) return 'border-yellow-200 bg-yellow-50';
    return 'border-green-200 bg-green-50';
  };

  const getStatusIcon = (log: SearchLog) => {
    if (log.error) return <AlertTriangle className="w-4 h-4 text-red-500" />;
    if (log.results_count === 0) return <Clock className="w-4 h-4 text-yellow-500" />;
    return <CheckCircle className="w-4 h-4 text-green-500" />;
  };

  if (loading) {
    return (
      <div className="card p-8">
        <div className="flex items-center justify-center py-8">
          <div className="spinner"></div>
          <span className="ml-3 text-gray-600">Loading search logs...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card p-8">
        <div className="text-center py-8">
          <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Error Loading Search Logs</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <button 
            onClick={loadSearchLogs}
            className="btn-primary"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="card p-8">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-3">
        <Search className="w-6 h-6 text-primary" />
        Search Debug Information
      </h2>
      
      {searchLogs.length === 0 ? (
        <p className="text-gray-600 text-center py-8">No search logs available</p>
      ) : (
        <>
          {/* Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <div className="text-2xl font-bold text-blue-700">{searchLogs.length}</div>
              <div className="text-sm text-blue-600">Total Searches</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <div className="text-2xl font-bold text-green-700">
                {searchLogs.filter(log => !log.error && log.results_count > 0).length}
              </div>
              <div className="text-sm text-green-600">Successful</div>
            </div>
            <div className="bg-red-50 p-4 rounded-lg border border-red-200">
              <div className="text-2xl font-bold text-red-700">
                {searchLogs.filter(log => log.error).length}
              </div>
              <div className="text-sm text-red-600">Failed</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <div className="text-2xl font-bold text-gray-700">
                {searchLogs.reduce((sum, log) => sum + log.results_count, 0)}
              </div>
              <div className="text-sm text-gray-600">Total Results</div>
            </div>
          </div>

          {/* Search Logs List */}
          <div className="space-y-4">
            {searchLogs.map((log, index) => (
              <div 
                key={index} 
                className={`border rounded-lg p-4 ${getStatusColor(log)}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-lg">{getSearchTypeIcon(log.search_type)}</span>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(log)}
                        <span className="font-medium text-gray-800">
                          {log.search_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </span>
                        <span className="text-sm text-gray-500">
                          {formatDuration(log.duration_ms)}
                        </span>
                      </div>
                    </div>
                    
                    <div className="mb-3">
                      <div className="text-sm text-gray-600 mb-1">Query:</div>
                      <div className="font-mono text-sm bg-white p-2 rounded border">
                        {log.query}
                      </div>
                    </div>

                    {expandedLogs[index] && (
                      <div className="space-y-3">
                        {/* Parameters */}
                        <div>
                          <div className="text-sm text-gray-600 mb-1">Parameters:</div>
                          <div className="font-mono text-xs bg-white p-2 rounded border">
                            <pre>{JSON.stringify(log.parameters, null, 2)}</pre>
                          </div>
                        </div>

                        {/* Processing Notes */}
                        {log.processing_notes && (
                          <div>
                            <div className="text-sm text-gray-600 mb-1">Notes:</div>
                            <div className="text-sm bg-white p-2 rounded border">
                              {log.processing_notes}
                            </div>
                          </div>
                        )}

                        {/* Error */}
                        {log.error && (
                          <div>
                            <div className="text-sm text-red-600 mb-1">Error:</div>
                            <div className="text-sm bg-red-100 p-2 rounded border border-red-200 text-red-700">
                              {log.error}
                            </div>
                          </div>
                        )}

                        {/* Results Count and Toggle */}
                        {log.results_count > 0 && (
                          <div className="flex items-center justify-between">
                            <div>
                              <span className="text-sm text-gray-600">
                                Results: {log.results_count}
                              </span>
                            </div>
                            <button
                              onClick={() => toggleResults(index)}
                              className="btn-secondary text-sm flex items-center gap-1"
                            >
                              {showResults[index] ? (
                                <>
                                  <EyeOff className="w-3 h-3" />
                                  Hide Results
                                </>
                              ) : (
                                <>
                                  <Eye className="w-3 h-3" />
                                  Show Results
                                </>
                              )}
                            </button>
                          </div>
                        )}

                        {/* Raw Results */}
                        {showResults[index] && log.results.length > 0 && (
                          <div>
                            <div className="text-sm text-gray-600 mb-2">Raw Results:</div>
                            <div className="max-h-96 overflow-y-auto">
                              {log.results.map((result, resultIndex) => (
                                <div key={resultIndex} className="mb-3 p-3 bg-white border rounded">
                                  <div className="font-medium text-sm mb-1">
                                    <a href={result.url} target="_blank" rel="noopener noreferrer" 
                                       className="text-blue-600 hover:underline">
                                      {result.title || 'Untitled'}
                                    </a>
                                  </div>
                                  <div className="text-xs text-gray-500 mb-2">{result.url}</div>
                                  <div className="text-sm text-gray-700 line-clamp-3">
                                    {result.content || result.raw_content || 'No content'}
                                  </div>
                                  {result.score && (
                                    <div className="text-xs text-gray-500 mt-1">
                                      Relevance: {(result.score * 100).toFixed(1)}%
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => toggleExpanded(index)}
                    className="ml-4 p-1 hover:bg-white hover:bg-opacity-50 rounded"
                  >
                    {expandedLogs[index] ? (
                      <ChevronUp className="w-4 h-4 text-gray-500" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-gray-500" />
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default SearchLogs;