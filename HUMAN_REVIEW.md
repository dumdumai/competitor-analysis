# Human Review System Documentation

## Overview

The Competitor Analysis System includes a sophisticated human review workflow built on LangGraph's persistent interrupts feature. This allows analyses to pause for human decisions and resume exactly where they left off.

## Architecture

### LangGraph Integration
- **Persistent Checkpoints**: PostgreSQL-backed checkpoints store workflow state
- **Conditional Routing**: Smart workflow routing based on quality issues
- **Resumable Interrupts**: Analyses can be paused and resumed without data loss

### Quality-Driven Interrupts
The system automatically triggers human review when:
- Critical data quality issues are detected
- Competitor relevance scores are below threshold
- Analysis confidence is low
- Retry limits are reached without success

## Workflow States

### 1. Normal Flow (No Human Review)
```
Search → Analysis → Quality Check → Report → Complete
```

### 2. Human Review Flow
```
Search → Analysis → Quality Check → [INTERRUPT] → Human Review → Report → Complete
```

### 3. Retry Flow (After Human Decision)
```
Human Review → [Retry Search] → Search → Analysis → Quality Check → Report → Complete
                     OR
Human Review → [Retry Analysis] → Analysis → Quality Check → Report → Complete
                     OR
Human Review → [Proceed] → Report → Complete
```

## API Endpoints

### Get Quality Review Data
```http
GET /api/v1/analysis/{request_id}/quality-review
```
Returns quality issues requiring human review.

**Response:**
```json
{
  "request_id": "string",
  "quality_issues": [
    {
      "type": "competitor_relevance",
      "severity": "high",
      "description": "Competitor X appears irrelevant to client industry",
      "affected_item": "Competitor X",
      "confidence": 0.3
    }
  ],
  "quality_summary": {
    "total_issues": 5,
    "critical_issues": 2,
    "average_quality": 0.7,
    "analysis_completed": true
  },
  "available_actions": [
    {"id": "proceed", "label": "Proceed with current results"},
    {"id": "retry_search", "label": "Retry search"},
    {"id": "retry_analysis", "label": "Retry analysis"}
  ]
}
```

### Submit Human Decision
```http
POST /api/v1/analysis/{request_id}/human-decision
```

**Request Body:**
```json
{
  "decision": "proceed|retry_search|retry_analysis|abort",
  "feedback": "Optional human feedback",
  "modified_params": {
    "max_competitors": 5,
    "industry_focus": "Updated focus"
  },
  "selected_issues": ["issue_id_1", "issue_id_2"]
}
```

**Response:**
```json
{
  "message": "Decision recorded successfully",
  "request_id": "string",
  "decision": "proceed",
  "workflow_resumed": true
}
```

### Check Interrupt Status
```http
GET /api/v1/analysis/{request_id}/interrupt-status
```

**Response:**
```json
{
  "request_id": "string",
  "is_interrupted": true,
  "interrupted_before": "human_review",
  "awaiting_human_review": true,
  "current_stage": "human_review",
  "progress": 75,
  "status": "in_progress"
}
```

### Get Quality Issues
```http
GET /api/v1/analysis/{request_id}/quality-issues
```
Returns detailed quality issues for human review.

## Frontend Integration

### Human Review UI Components

#### 1. Quality Issues Display
```typescript
interface QualityIssue {
  type: 'competitor_relevance' | 'data_quality' | 'analysis_confidence';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  affected_item: string;
  confidence: number;
  suggestion?: string;
}
```

#### 2. Decision Interface
```typescript
interface HumanDecision {
  decision: 'proceed' | 'retry_search' | 'retry_analysis' | 'abort';
  feedback?: string;
  modified_params?: Record<string, any>;
  selected_issues?: string[];
}
```

#### 3. Review Dashboard
- **Quality Score Visualization**: Charts showing quality metrics
- **Issue Categorization**: Grouped by severity and type
- **Competitor Relevance**: Visual indicator of relevance scores
- **Action Buttons**: Clear options for human decisions
- **Progress Tracking**: Real-time workflow progress

### WebSocket Updates
The system provides real-time updates via WebSocket:
```typescript
// Subscribe to analysis updates
const ws = new WebSocket(`ws://localhost:8000/ws/analysis/${analysisId}`);

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  if (update.stage === 'human_review') {
    // Show human review interface
    showHumanReviewModal(update.data);
  }
};
```

## Configuration

### Quality Thresholds
```python
# In backend/config/quality_config.py
QUALITY_THRESHOLDS = {
    'competitor_relevance': 0.7,
    'data_completeness': 0.8,
    'analysis_confidence': 0.6,
    'market_data_freshness': 0.9
}

HUMAN_REVIEW_TRIGGERS = {
    'critical_issues_count': 2,
    'low_quality_percentage': 0.4,
    'retry_limit_reached': True
}
```

## Error Handling

### Common Issues and Solutions

#### 1. Checkpoint Not Found
- **Issue**: Analysis state lost, cannot resume workflow
- **Solution**: Fallback to database state, notify user of potential data loss

#### 2. Human Review Timeout
- **Issue**: Analysis waiting for human decision too long
- **Solution**: Auto-proceed after configurable timeout (default: 24 hours)

#### 3. Invalid Human Decision
- **Issue**: Decision doesn't match available options
- **Solution**: Return error with valid options, maintain workflow state

## Testing

### Manual Testing
1. Start analysis with low-quality competitor data
2. Wait for human review interrupt
3. Check quality review endpoint
4. Submit various decisions (proceed, retry, abort)
5. Verify workflow resumes correctly

### Automated Testing
```python
async def test_human_review_workflow():
    # Start analysis with known quality issues
    analysis_id = await start_analysis_with_quality_issues()

    # Wait for human review interrupt
    status = await wait_for_interrupt(analysis_id)
    assert status['awaiting_human_review'] == True

    # Get quality review data
    review = await get_quality_review(analysis_id)
    assert len(review['quality_issues']) > 0

    # Submit human decision
    decision = {"decision": "proceed", "feedback": "Test feedback"}
    result = await submit_human_decision(analysis_id, decision)
    assert result['workflow_resumed'] == True

    # Wait for completion
    final_status = await wait_for_completion(analysis_id)
    assert final_status['status'] == 'completed'
```

## Best Practices

### For Developers
1. **Always check interrupt status** before resuming workflows
2. **Handle network failures** gracefully during human review
3. **Validate human decisions** before processing
4. **Log all human interactions** for audit trail

### For Users
1. **Review quality issues carefully** before making decisions
2. **Provide meaningful feedback** to improve future analyses
3. **Don't leave analyses in review state** for extended periods
4. **Understand retry implications** on analysis cost and time

## Monitoring

### Key Metrics
- Human review trigger rate
- Average review time
- Decision distribution (proceed vs retry)
- Quality improvement after retries
- Abandoned reviews (timeout rate)

### Logging
All human review interactions are logged with:
- Timestamp
- User ID (if available)
- Decision made
- Quality issues present
- Feedback provided
- Workflow outcome

## Future Enhancements

### Planned Features
1. **Multi-user Review**: Support for team-based review decisions
2. **Review Templates**: Pre-defined decision templates for common scenarios
3. **ML-Assisted Decisions**: AI suggestions for human review decisions
4. **Batch Review**: Review multiple analyses simultaneously
5. **Review Analytics**: Advanced analytics on review patterns and outcomes
