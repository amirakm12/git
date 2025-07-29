"""
Triage Agent
Handles initial request processing, classification, and routing
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import hashlib
import re
from collections import defaultdict

from ..core.config import SystemConfig

logger = logging.getLogger(__name__)

class RequestType(Enum):
    """Types of requests the triage agent can handle."""
    INFORMATION_REQUEST = "information_request"
    SYSTEM_CONTROL = "system_control"
    RESEARCH_QUERY = "research_query"
    TROUBLESHOOTING = "troubleshooting"
    WORKFLOW_MANAGEMENT = "workflow_management"
    STATUS_CHECK = "status_check"
    GENERAL_QUERY = "general_query"

class Priority(Enum):
    """Request priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5

class RequestStatus(Enum):
    """Request processing status."""
    RECEIVED = "received"
    ANALYZING = "analyzing"
    CLASSIFIED = "classified"
    ROUTED = "routed"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class TriageRequest:
    """Request data for triage processing."""
    request_id: str
    original_text: str
    request_type: RequestType
    priority: Priority
    status: RequestStatus
    timestamp: float
    context: Dict[str, Any]
    routing_target: Optional[str] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = None

@dataclass
class TriageResult:
    """Result of triage processing."""
    request_id: str
    classification: RequestType
    priority: Priority
    routing_target: str
    confidence: float
    processing_time: float
    extracted_entities: Dict[str, Any]
    recommended_actions: List[str]
    context_analysis: Dict[str, Any]

class TriageAgent:
    """Agent responsible for initial request triage and routing."""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.is_running = False
        
        # Request processing
        self.active_requests = {}
        self.request_history = []
        self.request_queue = asyncio.Queue()
        
        # Classification patterns
        self.classification_patterns = self._initialize_classification_patterns()
        self.entity_extractors = self._initialize_entity_extractors()
        self.routing_rules = self._initialize_routing_rules()
        
        # Performance metrics
        self.metrics = {
            'total_requests': 0,
            'successful_classifications': 0,
            'failed_classifications': 0,
            'average_processing_time': 0.0,
            'classification_accuracy': 0.0,
            'requests_by_type': defaultdict(int),
            'requests_by_priority': defaultdict(int)
        }
        
        logger.info("Triage Agent initialized")
    
    def _initialize_classification_patterns(self) -> Dict[RequestType, List[str]]:
        """Initialize patterns for request classification."""
        return {
            RequestType.INFORMATION_REQUEST: [
                r'\b(what|who|when|where|why|how)\b',
                r'\b(tell me|explain|describe|define)\b',
                r'\b(information|details|facts)\b',
                r'\b(learn|understand|know)\b'
            ],
            RequestType.SYSTEM_CONTROL: [
                r'\b(start|stop|restart|shutdown|pause|resume)\b',
                r'\b(enable|disable|activate|deactivate)\b',
                r'\b(configure|setup|install|update)\b',
                r'\b(system|service|process)\b'
            ],
            RequestType.RESEARCH_QUERY: [
                r'\b(research|investigate|analyze|study)\b',
                r'\b(compare|contrast|evaluate)\b',
                r'\b(trends|patterns|insights)\b',
                r'\b(literature|papers|studies)\b'
            ],
            RequestType.TROUBLESHOOTING: [
                r'\b(error|problem|issue|bug|fault)\b',
                r'\b(fix|solve|resolve|repair)\b',
                r'\b(troubleshoot|debug|diagnose)\b',
                r'\b(not working|broken|failed)\b'
            ],
            RequestType.WORKFLOW_MANAGEMENT: [
                r'\b(workflow|process|task|job)\b',
                r'\b(execute|run|schedule|queue)\b',
                r'\b(pipeline|automation|orchestration)\b',
                r'\b(batch|sequence|chain)\b'
            ],
            RequestType.STATUS_CHECK: [
                r'\b(status|health|state|condition)\b',
                r'\b(check|monitor|report|summary)\b',
                r'\b(running|active|available|online)\b',
                r'\b(performance|metrics|statistics)\b'
            ]
        }
    
    def _initialize_entity_extractors(self) -> Dict[str, str]:
        """Initialize entity extraction patterns."""
        return {
            'system_component': r'\b(agent|service|module|component|system)\s+(\w+)\b',
            'action_verb': r'\b(start|stop|restart|create|delete|update|get|set)\b',
            'time_reference': r'\b(now|today|tomorrow|yesterday|last|next)\s+(\w+)\b',
            'priority_indicator': r'\b(urgent|critical|important|high|low)\s+(priority)?\b',
            'workflow_name': r'\bworkflow\s+["\']?(\w+)["\']?\b',
            'file_path': r'["\']?([/\\][\w/\\.-]+)["\']?',
            'url': r'https?://[^\s]+',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'number': r'\b\d+(?:\.\d+)?\b'
        }
    
    def _initialize_routing_rules(self) -> Dict[RequestType, str]:
        """Initialize routing rules for different request types."""
        return {
            RequestType.INFORMATION_REQUEST: 'research_agent',
            RequestType.SYSTEM_CONTROL: 'system_controller',
            RequestType.RESEARCH_QUERY: 'research_agent',
            RequestType.TROUBLESHOOTING: 'diagnostic_agent',
            RequestType.WORKFLOW_MANAGEMENT: 'orchestration_agent',
            RequestType.STATUS_CHECK: 'monitoring_agent',
            RequestType.GENERAL_QUERY: 'research_agent'
        }
    
    async def initialize(self):
        """Initialize the triage agent."""
        logger.info("Initializing Triage Agent...")
        
        try:
            # Initialize ML models for classification (placeholder)
            await self._initialize_ml_models()
            
            # Load historical data for pattern learning
            await self._load_historical_patterns()
            
            logger.info("Triage Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Triage Agent: {e}")
            raise
    
    async def start(self):
        """Start the triage agent."""
        logger.info("Starting Triage Agent...")
        
        try:
            # Start background tasks
            self.background_tasks = {
                'request_processor': asyncio.create_task(self._request_processing_loop()),
                'metrics_collector': asyncio.create_task(self._metrics_collection_loop()),
                'pattern_learner': asyncio.create_task(self._pattern_learning_loop()),
                'cleanup_manager': asyncio.create_task(self._cleanup_management_loop())
            }
            
            self.is_running = True
            logger.info("Triage Agent started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Triage Agent: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the triage agent."""
        logger.info("Shutting down Triage Agent...")
        
        self.is_running = False
        
        # Cancel background tasks
        for task_name, task in self.background_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Cancelled {task_name}")
        
        # Save learned patterns
        await self._save_learned_patterns()
        
        logger.info("Triage Agent shutdown complete")
    
    async def process_request(self, request_text: str, context: Dict[str, Any] = None) -> TriageResult:
        """Process a request through triage analysis."""
        start_time = time.time()
        request_id = self._generate_request_id(request_text)
        
        logger.info(f"Processing triage request {request_id}: {request_text[:100]}...")
        
        # Create triage request
        triage_request = TriageRequest(
            request_id=request_id,
            original_text=request_text,
            request_type=RequestType.GENERAL_QUERY,  # Will be classified
            priority=Priority.NORMAL,  # Will be determined
            status=RequestStatus.RECEIVED,
            timestamp=time.time(),
            context=context or {},
            metadata={}
        )
        
        self.active_requests[request_id] = triage_request
        self.metrics['total_requests'] += 1
        
        try:
            # Phase 1: Text preprocessing
            processed_text = await self._preprocess_text(request_text)
            
            # Phase 2: Request classification
            triage_request.status = RequestStatus.ANALYZING
            classification_result = await self._classify_request(processed_text, context)
            
            triage_request.request_type = classification_result['type']
            triage_request.confidence = classification_result['confidence']
            triage_request.status = RequestStatus.CLASSIFIED
            
            # Phase 3: Priority determination
            priority = await self._determine_priority(processed_text, classification_result, context)
            triage_request.priority = priority
            
            # Phase 4: Entity extraction
            entities = await self._extract_entities(processed_text)
            
            # Phase 5: Context analysis
            context_analysis = await self._analyze_context(processed_text, context, entities)
            
            # Phase 6: Routing decision
            routing_target = await self._determine_routing(
                triage_request.request_type, 
                entities, 
                context_analysis
            )
            triage_request.routing_target = routing_target
            triage_request.status = RequestStatus.ROUTED
            
            # Phase 7: Generate recommendations
            recommendations = await self._generate_recommendations(
                triage_request.request_type,
                entities,
                context_analysis
            )
            
            # Create result
            result = TriageResult(
                request_id=request_id,
                classification=triage_request.request_type,
                priority=triage_request.priority,
                routing_target=routing_target,
                confidence=triage_request.confidence,
                processing_time=time.time() - start_time,
                extracted_entities=entities,
                recommended_actions=recommendations,
                context_analysis=context_analysis
            )
            
            triage_request.status = RequestStatus.COMPLETED
            
            # Update metrics
            self.metrics['successful_classifications'] += 1
            self.metrics['requests_by_type'][triage_request.request_type.value] += 1
            self.metrics['requests_by_priority'][triage_request.priority.value] += 1
            
            # Update average processing time
            total_successful = self.metrics['successful_classifications']
            if total_successful > 1:
                self.metrics['average_processing_time'] = (
                    (self.metrics['average_processing_time'] * (total_successful - 1) + result.processing_time) / total_successful
                )
            else:
                self.metrics['average_processing_time'] = result.processing_time
            
            # Move to history
            self.request_history.append(triage_request)
            
            logger.info(f"Completed triage for request {request_id}: "
                       f"{result.classification.value} -> {result.routing_target}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing triage request {request_id}: {e}")
            
            triage_request.status = RequestStatus.FAILED
            self.metrics['failed_classifications'] += 1
            
            # Return failed result
            return TriageResult(
                request_id=request_id,
                classification=RequestType.GENERAL_QUERY,
                priority=Priority.NORMAL,
                routing_target='research_agent',
                confidence=0.0,
                processing_time=time.time() - start_time,
                extracted_entities={},
                recommended_actions=['Manual review required'],
                context_analysis={'error': str(e)}
            )
        
        finally:
            # Remove from active requests
            if request_id in self.active_requests:
                del self.active_requests[request_id]
    
    async def _preprocess_text(self, text: str) -> str:
        """Preprocess text for analysis."""
        # Convert to lowercase
        processed = text.lower().strip()
        
        # Remove extra whitespace
        processed = re.sub(r'\s+', ' ', processed)
        
        # Remove special characters (but keep important punctuation)
        processed = re.sub(r'[^\w\s\-.,!?@#$%^&*()+=\[\]{}|\\:";\'<>/]', '', processed)
        
        return processed
    
    async def _classify_request(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Classify the request type."""
        classification_scores = {}
        
        # Pattern-based classification
        for request_type, patterns in self.classification_patterns.items():
            score = 0
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    matches += 1
                    score += 1
            
            # Normalize score
            if patterns:
                classification_scores[request_type] = score / len(patterns)
        
        # Context-based adjustments
        if context:
            # Boost certain types based on context
            if context.get('source') == 'system_monitor':
                classification_scores[RequestType.STATUS_CHECK] = classification_scores.get(RequestType.STATUS_CHECK, 0) + 0.3
            
            if context.get('urgency') == 'high':
                classification_scores[RequestType.TROUBLESHOOTING] = classification_scores.get(RequestType.TROUBLESHOOTING, 0) + 0.2
        
        # Find best classification
        if classification_scores:
            best_type = max(classification_scores, key=classification_scores.get)
            confidence = classification_scores[best_type]
        else:
            best_type = RequestType.GENERAL_QUERY
            confidence = 0.5
        
        return {
            'type': best_type,
            'confidence': min(confidence, 1.0),
            'scores': classification_scores
        }
    
    async def _determine_priority(self, text: str, classification: Dict[str, Any], 
                                context: Dict[str, Any] = None) -> Priority:
        """Determine request priority."""
        priority_score = 0
        
        # Keywords that indicate priority
        urgent_keywords = ['urgent', 'critical', 'emergency', 'asap', 'immediately']
        high_keywords = ['important', 'high', 'priority', 'soon', 'quickly']
        low_keywords = ['low', 'later', 'when possible', 'no rush']
        
        text_lower = text.lower()
        
        # Check for explicit priority indicators
        if any(keyword in text_lower for keyword in urgent_keywords):
            priority_score += 4
        elif any(keyword in text_lower for keyword in high_keywords):
            priority_score += 2
        elif any(keyword in text_lower for keyword in low_keywords):
            priority_score -= 2
        
        # Request type influences priority
        request_type = classification['type']
        if request_type == RequestType.TROUBLESHOOTING:
            priority_score += 2
        elif request_type == RequestType.SYSTEM_CONTROL:
            priority_score += 1
        elif request_type == RequestType.STATUS_CHECK:
            priority_score += 1
        
        # Context influences priority
        if context:
            if context.get('source') == 'error_handler':
                priority_score += 3
            if context.get('system_health') == 'degraded':
                priority_score += 2
        
        # Map score to priority level
        if priority_score >= 4:
            return Priority.CRITICAL
        elif priority_score >= 3:
            return Priority.URGENT
        elif priority_score >= 1:
            return Priority.HIGH
        elif priority_score >= 0:
            return Priority.NORMAL
        else:
            return Priority.LOW
    
    async def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities from the text."""
        entities = {}
        
        for entity_type, pattern in self.entity_extractors.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities[entity_type] = matches
        
        # Additional entity extraction logic
        
        # Extract quoted strings (might be filenames, commands, etc.)
        quoted_strings = re.findall(r'["\']([^"\']+)["\']', text)
        if quoted_strings:
            entities['quoted_strings'] = quoted_strings
        
        # Extract system components mentioned
        system_components = re.findall(r'\b(agent|service|module|component|system|server|database|api)\b', text, re.IGNORECASE)
        if system_components:
            entities['system_components'] = list(set(system_components))
        
        return entities
    
    async def _analyze_context(self, text: str, context: Dict[str, Any] = None, 
                             entities: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze request context."""
        analysis = {
            'text_length': len(text),
            'word_count': len(text.split()),
            'complexity': self._calculate_text_complexity(text),
            'sentiment': self._analyze_sentiment(text),
            'technical_level': self._assess_technical_level(text, entities or {})
        }
        
        # Add context information if available
        if context:
            analysis['context_provided'] = True
            analysis['context_keys'] = list(context.keys())
            
            # Analyze context relevance
            if 'timestamp' in context:
                analysis['time_sensitive'] = time.time() - context['timestamp'] < 3600  # Less than 1 hour
            
            if 'user_id' in context:
                analysis['user_request'] = True
            
            if 'system_state' in context:
                analysis['system_context'] = context['system_state']
        else:
            analysis['context_provided'] = False
        
        return analysis
    
    def _calculate_text_complexity(self, text: str) -> float:
        """Calculate text complexity score."""
        words = text.split()
        if not words:
            return 0.0
        
        # Simple complexity metrics
        avg_word_length = sum(len(word) for word in words) / len(words)
        sentence_count = len(re.findall(r'[.!?]+', text))
        avg_sentence_length = len(words) / max(sentence_count, 1)
        
        # Technical terms increase complexity
        technical_terms = len(re.findall(r'\b(system|process|algorithm|configuration|implementation|architecture)\b', text, re.IGNORECASE))
        
        # Normalize to 0-1 scale
        complexity = min((avg_word_length / 10 + avg_sentence_length / 20 + technical_terms / 10), 1.0)
        
        return complexity
    
    def _analyze_sentiment(self, text: str) -> str:
        """Analyze text sentiment (simplified)."""
        positive_words = ['good', 'great', 'excellent', 'perfect', 'working', 'success', 'complete']
        negative_words = ['bad', 'terrible', 'broken', 'error', 'fail', 'problem', 'issue', 'wrong']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if negative_count > positive_count:
            return 'negative'
        elif positive_count > negative_count:
            return 'positive'
        else:
            return 'neutral'
    
    def _assess_technical_level(self, text: str, entities: Dict[str, Any]) -> str:
        """Assess technical level of the request."""
        technical_indicators = [
            'api', 'database', 'server', 'configuration', 'implementation',
            'algorithm', 'architecture', 'deployment', 'optimization',
            'debugging', 'logging', 'monitoring', 'authentication'
        ]
        
        text_lower = text.lower()
        technical_count = sum(1 for term in technical_indicators if term in text_lower)
        
        # Entity-based technical assessment
        if entities.get('system_components') or entities.get('file_path'):
            technical_count += 2
        
        if technical_count >= 3:
            return 'high'
        elif technical_count >= 1:
            return 'medium'
        else:
            return 'low'
    
    async def _determine_routing(self, request_type: RequestType, entities: Dict[str, Any], 
                               context_analysis: Dict[str, Any]) -> str:
        """Determine where to route the request."""
        # Default routing based on request type
        default_target = self.routing_rules.get(request_type, 'research_agent')
        
        # Override routing based on entities and context
        if entities.get('system_components'):
            if any('workflow' in comp.lower() for comp in entities['system_components']):
                return 'orchestration_agent'
            elif any('monitor' in comp.lower() for comp in entities['system_components']):
                return 'monitoring_agent'
        
        # Route based on technical level
        if context_analysis.get('technical_level') == 'high':
            if request_type == RequestType.TROUBLESHOOTING:
                return 'technical_support_agent'
        
        # Route based on urgency
        if context_analysis.get('time_sensitive'):
            return 'priority_handler'
        
        return default_target
    
    async def _generate_recommendations(self, request_type: RequestType, 
                                      entities: Dict[str, Any],
                                      context_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommended actions for the request."""
        recommendations = []
        
        # Type-specific recommendations
        if request_type == RequestType.INFORMATION_REQUEST:
            recommendations.extend([
                "Search knowledge base for relevant information",
                "Consult documentation and resources",
                "Provide comprehensive and accurate response"
            ])
        elif request_type == RequestType.SYSTEM_CONTROL:
            recommendations.extend([
                "Verify user permissions for system operations",
                "Check system state before executing commands",
                "Log all system control actions"
            ])
        elif request_type == RequestType.TROUBLESHOOTING:
            recommendations.extend([
                "Gather system logs and diagnostic information",
                "Identify root cause of the issue",
                "Provide step-by-step resolution guidance"
            ])
        elif request_type == RequestType.RESEARCH_QUERY:
            recommendations.extend([
                "Conduct comprehensive research on the topic",
                "Analyze multiple sources and perspectives",
                "Synthesize findings into coherent response"
            ])
        
        # Context-based recommendations
        if context_analysis.get('technical_level') == 'high':
            recommendations.append("Provide technical details and implementation specifics")
        elif context_analysis.get('technical_level') == 'low':
            recommendations.append("Use clear, non-technical language in response")
        
        if context_analysis.get('sentiment') == 'negative':
            recommendations.append("Address concerns with empathy and provide reassurance")
        
        # Entity-based recommendations
        if entities.get('file_path'):
            recommendations.append("Verify file paths and permissions")
        
        if entities.get('url'):
            recommendations.append("Validate URLs and check accessibility")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    async def _request_processing_loop(self):
        """Background loop for processing queued requests."""
        while self.is_running:
            try:
                # This could handle batch processing or background analysis
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in request processing loop: {e}")
                await asyncio.sleep(1)
    
    async def _metrics_collection_loop(self):
        """Background loop for metrics collection."""
        while self.is_running:
            try:
                if self.metrics['total_requests'] > 0:
                    success_rate = (self.metrics['successful_classifications'] / 
                                  self.metrics['total_requests']) * 100
                    
                    logger.info(f"Triage Agent Metrics - "
                              f"Total Requests: {self.metrics['total_requests']}, "
                              f"Success Rate: {success_rate:.1f}%, "
                              f"Avg Processing Time: {self.metrics['average_processing_time']:.3f}s")
                
                await asyncio.sleep(300)  # Log every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(300)
    
    async def _pattern_learning_loop(self):
        """Background loop for learning from processed requests."""
        while self.is_running:
            try:
                # Analyze recent requests for pattern improvements
                if len(self.request_history) >= 10:
                    await self._analyze_classification_patterns()
                
                await asyncio.sleep(3600)  # Analyze every hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in pattern learning: {e}")
                await asyncio.sleep(3600)
    
    async def _cleanup_management_loop(self):
        """Background loop for cleanup management."""
        while self.is_running:
            try:
                # Clean up old request history
                current_time = time.time()
                max_age = 86400  # 24 hours
                max_history_size = 1000  # Maximum number of history entries
                
                # Clean by age
                self.request_history = [
                    req for req in self.request_history
                    if current_time - req.timestamp <= max_age
                ]
                
                # Clean by size (keep most recent entries)
                if len(self.request_history) > max_history_size:
                    self.request_history = self.request_history[-max_history_size:]
                
                # Also clean classification history
                if len(self.classification_history) > max_history_size:
                    self.classification_history = self.classification_history[-max_history_size:]
                
                await asyncio.sleep(3600)  # Clean every hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup management: {e}")
                await asyncio.sleep(3600)
    
    async def _initialize_ml_models(self):
        """Initialize ML models for classification."""
        try:
            # Initialize basic classification models
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.naive_bayes import MultinomialNB
            from sklearn.pipeline import Pipeline
            
            # Create a simple text classification pipeline
            self.ml_classifier = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=1000, stop_words='english')),
                ('classifier', MultinomialNB())
            ])
            
            # Train with basic examples if no pre-trained model exists
            sample_texts = [
                "urgent help needed with system crash",
                "how do I configure the settings",
                "error message appears when starting",
                "request for new feature implementation",
                "system performance is very slow",
                "need information about documentation"
            ]
            sample_labels = [
                "urgent", "support", "error", "feature", "performance", "information"
            ]
            
            self.ml_classifier.fit(sample_texts, sample_labels)
            logger.info("ML classification models initialized successfully")
            
        except ImportError:
            logger.warning("scikit-learn not available, using rule-based classification only")
            self.ml_classifier = None
        except Exception as e:
            logger.error(f"Error initializing ML models: {e}")
            self.ml_classifier = None
    
    async def _load_historical_patterns(self):
        """Load historical patterns for classification improvement."""
        try:
            patterns_file = self.config.data_dir / "triage_patterns.json"
            
            if patterns_file.exists():
                with open(patterns_file, 'r') as f:
                    self.historical_patterns = json.load(f)
                logger.info(f"Loaded {len(self.historical_patterns)} historical patterns")
            else:
                # Initialize with default patterns
                self.historical_patterns = {
                    'urgent_keywords': ['urgent', 'critical', 'emergency', 'crash', 'down', 'failure'],
                    'support_keywords': ['help', 'how to', 'configure', 'setup', 'install'],
                    'error_keywords': ['error', 'exception', 'failed', 'broken', 'bug'],
                    'feature_keywords': ['feature', 'enhancement', 'improvement', 'add', 'new'],
                    'performance_keywords': ['slow', 'performance', 'optimization', 'speed', 'lag'],
                    'information_keywords': ['documentation', 'info', 'explain', 'what is', 'guide']
                }
                await self._save_learned_patterns()
                
        except Exception as e:
            logger.error(f"Error loading historical patterns: {e}")
            self.historical_patterns = {}
    
    async def _save_learned_patterns(self):
        """Save learned patterns for future use."""
        try:
            patterns_file = self.config.data_dir / "triage_patterns.json"
            
            with open(patterns_file, 'w') as f:
                json.dump(self.historical_patterns, f, indent=2)
            
            logger.info("Saved learned patterns to file")
            
        except Exception as e:
            logger.error(f"Error saving learned patterns: {e}")
    
    async def _analyze_classification_patterns(self):
        """Analyze recent classifications to improve patterns."""
        try:
            # Analyze recent classifications to improve patterns
            if len(self.classification_history) < 10:
                return
            
            # Get recent classifications
            recent_classifications = list(self.classification_history)[-50:]
            
            # Analyze keyword effectiveness
            keyword_performance = {}
            
            for classification in recent_classifications:
                request_text = classification.get('request_text', '').lower()
                classified_type = classification.get('type')
                confidence = classification.get('confidence', 0)
                
                # Extract keywords that led to high-confidence classifications
                if confidence > 0.8:
                    words = request_text.split()
                    for word in words:
                        if len(word) > 3:  # Skip short words
                            if word not in keyword_performance:
                                keyword_performance[word] = {'count': 0, 'types': {}}
                            keyword_performance[word]['count'] += 1
                            if classified_type not in keyword_performance[word]['types']:
                                keyword_performance[word]['types'][classified_type] = 0
                            keyword_performance[word]['types'][classified_type] += 1
            
            # Update patterns with high-performing keywords
            for word, performance in keyword_performance.items():
                if performance['count'] >= 3:  # Word appeared in at least 3 high-confidence classifications
                    # Find the most common type for this word
                    most_common_type = max(performance['types'], key=performance['types'].get)
                    type_key = f"{most_common_type}_keywords"
                    
                    if type_key in self.historical_patterns:
                        if word not in self.historical_patterns[type_key]:
                            self.historical_patterns[type_key].append(word)
                            logger.info(f"Added learned keyword '{word}' to {most_common_type} patterns")
            
            # Save updated patterns
            await self._save_learned_patterns()
            
        except Exception as e:
            logger.error(f"Error analyzing classification patterns: {e}")
    
    def _generate_request_id(self, text: str) -> str:
        """Generate unique request ID."""
        content = f"{text[:50]}_{time.time()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    # Public API methods
    
    async def health_check(self) -> str:
        """Perform health check."""
        try:
            # Test basic triage functionality
            test_result = await self.process_request("test health check request")
            
            if test_result.confidence > 0:
                return "healthy"
            else:
                return "degraded"
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return "unhealthy"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get triage agent statistics."""
        return {
            'metrics': self.metrics.copy(),
            'active_requests': len(self.active_requests),
            'request_history_size': len(self.request_history),
            'classification_patterns': len(self.classification_patterns),
            'routing_rules': len(self.routing_rules)
        }
    
    def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific request."""
        if request_id in self.active_requests:
            request = self.active_requests[request_id]
            return {
                'request_id': request_id,
                'status': request.status.value,
                'type': request.request_type.value,
                'priority': request.priority.value,
                'confidence': request.confidence,
                'routing_target': request.routing_target
            }
        
        # Check history
        for request in self.request_history:
            if request.request_id == request_id:
                return {
                    'request_id': request_id,
                    'status': request.status.value,
                    'type': request.request_type.value,
                    'priority': request.priority.value,
                    'confidence': request.confidence,
                    'routing_target': request.routing_target
                }
        
        return None
    
    async def restart(self):
        """Restart the triage agent."""
        logger.info("Restarting Triage Agent...")
        await self.shutdown()
        await asyncio.sleep(1)
        await self.initialize()
        await self.start()