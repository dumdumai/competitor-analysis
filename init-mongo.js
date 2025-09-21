// MongoDB initialization script

print('Starting database initialization...');

// Switch to the competitor_analysis database
db = db.getSiblingDB('competitor_analysis');

// Create collections with validation
db.createCollection('analyses', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['request_id', 'client_company', 'industry', 'status'],
      properties: {
        request_id: {
          bsonType: 'string',
          description: 'Unique request identifier'
        },
        client_company: {
          bsonType: 'string',
          minLength: 1,
          description: 'Client company name'
        },
        industry: {
          bsonType: 'string',
          minLength: 1,
          description: 'Industry sector'
        },
        status: {
          bsonType: 'string',
          enum: ['pending', 'in_progress', 'completed', 'failed'],
          description: 'Analysis status'
        },
        progress: {
          bsonType: 'int',
          minimum: 0,
          maximum: 100,
          description: 'Progress percentage'
        }
      }
    }
  }
});

db.createCollection('reports', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['analysis_id', 'title', 'client_company', 'industry'],
      properties: {
        analysis_id: {
          bsonType: 'string',
          description: 'Associated analysis ID'
        },
        title: {
          bsonType: 'string',
          minLength: 1,
          description: 'Report title'
        },
        client_company: {
          bsonType: 'string',
          minLength: 1,
          description: 'Client company name'
        },
        industry: {
          bsonType: 'string',
          minLength: 1,
          description: 'Industry sector'
        }
      }
    }
  }
});

db.createCollection('agent_states');

// Create indexes for better performance
print('Creating indexes...');

// Analyses collection indexes
db.analyses.createIndex({ "request_id": 1 }, { unique: true });
db.analyses.createIndex({ "client_company": 1 });
db.analyses.createIndex({ "industry": 1 });
db.analyses.createIndex({ "status": 1 });
db.analyses.createIndex({ "created_at": -1 });

// Reports collection indexes
db.reports.createIndex({ "analysis_id": 1 });
db.reports.createIndex({ "client_company": 1 });
db.reports.createIndex({ "industry": 1 });
db.reports.createIndex({ "created_at": -1 });

// Agent states collection indexes
db.agent_states.createIndex({ "request_id": 1 }, { unique: true });
db.agent_states.createIndex({ "status": 1 });
db.agent_states.createIndex({ "updated_at": -1 });

print('Database initialization completed successfully!');

// Insert a sample document for testing (optional)
if (db.analyses.countDocuments() === 0) {
  print('Inserting sample data...');
  
  db.analyses.insertOne({
    request_id: 'sample_analysis_001',
    client_company: 'Sample Company',
    industry: 'Technology',
    status: 'completed',
    progress: 100,
    competitors: [
      {
        name: 'Competitor A',
        description: 'Leading technology company',
        business_model: 'B2B SaaS',
        strengths: ['Strong brand', 'Large customer base'],
        weaknesses: ['High pricing']
      }
    ],
    recommendations: [
      'Focus on pricing competitiveness',
      'Strengthen brand positioning',
      'Expand customer acquisition channels'
    ],
    created_at: new Date(),
    updated_at: new Date(),
    completed_at: new Date()
  });
  
  print('Sample data inserted.');
}

print('All initialization tasks completed!');