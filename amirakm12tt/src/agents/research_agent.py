"""
Research Agent
Conducts comprehensive research, analysis, and knowledge synthesis
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import hashlib
from collections import defaultdict
import re

from ..core.config import SystemConfig
from ..ai.rag_engine import RAGEngine, QueryResult
from ..ai.speculative_decoder import SpeculativeDecoder, DecodingRequest, SpeculationStrategy

logger = logging.getLogger(__name__)

class ResearchType(Enum):
    """Types of research tasks."""
    LITERATURE_REVIEW = "literature_review"
    COMPARATIVE_ANALYSIS = "comparative_analysis"
    TECHNICAL_INVESTIGATION = "technical_investigation"
    TREND_ANALYSIS = "trend_analysis"
    PROBLEM_SOLVING = "problem_solving"
    DATA_SYNTHESIS = "data_synthesis"

class ResearchStatus(Enum):
    """Research task status."""
    INITIATED = "initiated"
    GATHERING = "gathering"
    ANALYZING = "analyzing"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ResearchTask:
    """Research task definition."""
    task_id: str
    query: str
    research_type: ResearchType
    depth_level: int  # 1-5, where 5 is most comprehensive
    time_limit: float
    required_sources: List[str]
    metadata: Dict[str, Any]

@dataclass
class ResearchResult:
    """Comprehensive research result."""
    task_id: str
    original_query: str
    research_type: ResearchType
    findings: List[Dict[str, Any]]
    synthesis: str
    confidence_score: float
    sources_consulted: List[str]
    processing_time: float
    status: ResearchStatus
    metadata: Dict[str, Any]

class ResearchAgent:
    """Agent specialized in comprehensive research and analysis."""
    
    def __init__(self, config: SystemConfig, rag_engine: RAGEngine, speculative_decoder: SpeculativeDecoder):
        self.config = config
        self.rag_engine = rag_engine
        self.speculative_decoder = speculative_decoder
        self.is_running = False
        
        # Research management
        self.active_research = {}
        self.completed_research = {}
        self.research_queue = asyncio.Queue()
        
        # Knowledge synthesis
        self.synthesis_templates = self._initialize_synthesis_templates()
        self.research_strategies = self._initialize_research_strategies()
        
        # Performance tracking
        self.metrics = {
            'total_research_tasks': 0,
            'completed_tasks': 0,
            'average_processing_time': 0.0,
            'average_confidence_score': 0.0,
            'research_by_type': defaultdict(int),
            'success_rate': 0.0
        }
        
        logger.info("Research Agent initialized")
    
    def _initialize_synthesis_templates(self) -> Dict[ResearchType, str]:
        """Initialize templates for different research types."""
        return {
            ResearchType.LITERATURE_REVIEW: """
# Literature Review: {topic}

## Overview
{overview}

## Key Findings
{key_findings}

## Analysis
{analysis}

## Conclusions
{conclusions}

## Sources
{sources}
""",
            ResearchType.COMPARATIVE_ANALYSIS: """
# Comparative Analysis: {topic}

## Comparison Framework
{framework}

## Key Differences
{differences}

## Similarities
{similarities}

## Evaluation
{evaluation}

## Recommendations
{recommendations}

## Sources
{sources}
""",
            ResearchType.TECHNICAL_INVESTIGATION: """
# Technical Investigation: {topic}

## Problem Statement
{problem}

## Technical Analysis
{technical_analysis}

## Solutions Identified
{solutions}

## Implementation Considerations
{implementation}

## Conclusion
{conclusion}

## References
{references}
""",
            ResearchType.TREND_ANALYSIS: """
# Trend Analysis: {topic}

## Current State
{current_state}

## Historical Context
{historical_context}

## Emerging Trends
{trends}

## Future Projections
{projections}

## Implications
{implications}

## Sources
{sources}
""",
            ResearchType.PROBLEM_SOLVING: """
# Problem-Solving Analysis: {topic}

## Problem Definition
{problem_definition}

## Root Cause Analysis
{root_causes}

## Solution Options
{solutions}

## Recommended Approach
{recommendation}

## Implementation Plan
{implementation}

## Risk Assessment
{risks}

## References
{references}
""",
            ResearchType.DATA_SYNTHESIS: """
# Data Synthesis: {topic}

## Data Sources
{data_sources}

## Methodology
{methodology}

## Key Insights
{insights}

## Patterns Identified
{patterns}

## Synthesis
{synthesis}

## Limitations
{limitations}

## Sources
{sources}
"""
        }
    
    def _initialize_research_strategies(self) -> Dict[ResearchType, Dict[str, Any]]:
        """Initialize research strategies for different types."""
        return {
            ResearchType.LITERATURE_REVIEW: {
                'queries_per_depth': {1: 3, 2: 5, 3: 8, 4: 12, 5: 20},
                'synthesis_approach': 'comprehensive_overview',
                'min_sources': 5
            },
            ResearchType.COMPARATIVE_ANALYSIS: {
                'queries_per_depth': {1: 4, 2: 6, 3: 10, 4: 15, 5: 25},
                'synthesis_approach': 'comparative_framework',
                'min_sources': 6
            },
            ResearchType.TECHNICAL_INVESTIGATION: {
                'queries_per_depth': {1: 3, 2: 5, 3: 8, 4: 12, 5: 18},
                'synthesis_approach': 'technical_analysis',
                'min_sources': 4
            },
            ResearchType.TREND_ANALYSIS: {
                'queries_per_depth': {1: 4, 2: 7, 3: 12, 4: 18, 5: 30},
                'synthesis_approach': 'temporal_analysis',
                'min_sources': 8
            },
            ResearchType.PROBLEM_SOLVING: {
                'queries_per_depth': {1: 3, 2: 5, 3: 8, 4: 12, 5: 20},
                'synthesis_approach': 'solution_oriented',
                'min_sources': 5
            },
            ResearchType.DATA_SYNTHESIS: {
                'queries_per_depth': {1: 5, 2: 8, 3: 12, 4: 20, 5: 35},
                'synthesis_approach': 'data_integration',
                'min_sources': 10
            }
        }
    
    async def initialize(self):
        """Initialize the research agent."""
        logger.info("Initializing Research Agent...")
        
        try:
            # Initialize research knowledge base
            await self._initialize_research_kb()
            
            # Load research templates and strategies
            await self._load_research_templates()
            
            logger.info("Research Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Research Agent: {e}")
            raise
    
    async def start(self):
        """Start the research agent."""
        logger.info("Starting Research Agent...")
        
        try:
            # Start background tasks
            self.background_tasks = {
                'research_processor': asyncio.create_task(self._research_processing_loop()),
                'metrics_collector': asyncio.create_task(self._metrics_collection_loop()),
                'knowledge_updater': asyncio.create_task(self._knowledge_update_loop()),
                'quality_assessor': asyncio.create_task(self._quality_assessment_loop())
            }
            
            self.is_running = True
            logger.info("Research Agent started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Research Agent: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the research agent."""
        logger.info("Shutting down Research Agent...")
        
        self.is_running = False
        
        # Cancel background tasks
        for task_name, task in self.background_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Cancelled {task_name}")
        
        # Save research results
        await self._save_research_results()
        
        logger.info("Research Agent shutdown complete")
    
    async def conduct_research(self, query: str, research_type: ResearchType = None, 
                             depth_level: int = 3, time_limit: float = 300.0,
                             metadata: Dict[str, Any] = None) -> ResearchResult:
        """Conduct comprehensive research on a topic."""
        start_time = time.time()
        task_id = self._generate_task_id(query)
        
        # Determine research type if not specified
        if research_type is None:
            research_type = self._classify_research_type(query)
        
        # Create research task
        research_task = ResearchTask(
            task_id=task_id,
            query=query,
            research_type=research_type,
            depth_level=depth_level,
            time_limit=time_limit,
            required_sources=[],
            metadata=metadata or {}
        )
        
        logger.info(f"Starting research task {task_id}: {query}")
        
        try:
            # Add to active research
            self.active_research[task_id] = {
                'task': research_task,
                'status': ResearchStatus.INITIATED,
                'start_time': start_time,
                'findings': []
            }
            
            # Phase 1: Information Gathering
            findings = await self._gather_information(research_task)
            
            # Phase 2: Analysis
            analyzed_findings = await self._analyze_findings(research_task, findings)
            
            # Phase 3: Synthesis
            synthesis = await self._synthesize_research(research_task, analyzed_findings)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(analyzed_findings, synthesis)
            
            # Create research result
            research_result = ResearchResult(
                task_id=task_id,
                original_query=query,
                research_type=research_type,
                findings=analyzed_findings,
                synthesis=synthesis,
                confidence_score=confidence_score,
                sources_consulted=self._extract_sources(analyzed_findings),
                processing_time=time.time() - start_time,
                status=ResearchStatus.COMPLETED,
                metadata={
                    'depth_level': depth_level,
                    'findings_count': len(analyzed_findings),
                    **(metadata or {})
                }
            )
            
            # Store completed research
            self.completed_research[task_id] = research_result
            
            # Remove from active research
            if task_id in self.active_research:
                del self.active_research[task_id]
            
            # Update metrics
            self._update_metrics(research_result)
            
            logger.info(f"Completed research task {task_id} in {research_result.processing_time:.2f}s")
            return research_result
            
        except Exception as e:
            logger.error(f"Error in research task {task_id}: {e}")
            
            # Create failed result
            failed_result = ResearchResult(
                task_id=task_id,
                original_query=query,
                research_type=research_type,
                findings=[],
                synthesis=f"Research failed: {str(e)}",
                confidence_score=0.0,
                sources_consulted=[],
                processing_time=time.time() - start_time,
                status=ResearchStatus.FAILED,
                metadata={'error': str(e), **(metadata or {})}
            )
            
            self.completed_research[task_id] = failed_result
            
            # Remove from active research
            if task_id in self.active_research:
                del self.active_research[task_id]
            
            return failed_result
    
    def _classify_research_type(self, query: str) -> ResearchType:
        """Classify the type of research based on the query."""
        query_lower = query.lower()
        
        # Pattern matching for research type classification
        patterns = {
            ResearchType.LITERATURE_REVIEW: [
                r'literature review', r'research overview', r'survey of',
                r'what is known about', r'current state of'
            ],
            ResearchType.COMPARATIVE_ANALYSIS: [
                r'compare', r'comparison', r'versus', r'vs\.', r'differences',
                r'similarities', r'contrast', r'evaluate options'
            ],
            ResearchType.TECHNICAL_INVESTIGATION: [
                r'how does', r'technical', r'implementation', r'architecture',
                r'system design', r'engineering', r'algorithm'
            ],
            ResearchType.TREND_ANALYSIS: [
                r'trends', r'future of', r'evolution', r'forecast',
                r'prediction', r'emerging', r'development'
            ],
            ResearchType.PROBLEM_SOLVING: [
                r'how to solve', r'solution', r'fix', r'resolve',
                r'troubleshoot', r'problem', r'issue'
            ],
            ResearchType.DATA_SYNTHESIS: [
                r'analyze data', r'synthesis', r'integrate', r'combine',
                r'meta-analysis', r'aggregate'
            ]
        }
        
        # Score each type
        type_scores = {}
        for research_type, type_patterns in patterns.items():
            score = 0
            for pattern in type_patterns:
                if re.search(pattern, query_lower):
                    score += 1
            type_scores[research_type] = score
        
        # Return highest scoring type, or default to literature review
        if max(type_scores.values()) > 0:
            return max(type_scores, key=type_scores.get)
        else:
            return ResearchType.LITERATURE_REVIEW
    
    async def _gather_information(self, research_task: ResearchTask) -> List[Dict[str, Any]]:
        """Gather information from various sources."""
        logger.info(f"Gathering information for task {research_task.task_id}")
        
        # Update status
        if research_task.task_id in self.active_research:
            self.active_research[research_task.task_id]['status'] = ResearchStatus.GATHERING
        
        strategy = self.research_strategies[research_task.research_type]
        num_queries = strategy['queries_per_depth'][research_task.depth_level]
        
        # Generate research queries
        research_queries = await self._generate_research_queries(
            research_task.query, 
            research_task.research_type, 
            num_queries
        )
        
        findings = []
        
        # Execute queries in parallel (with rate limiting)
        semaphore = asyncio.Semaphore(3)  # Limit concurrent queries
        
        async def execute_query(query):
            async with semaphore:
                try:
                    result = await self.rag_engine.query(query)
                    return {
                        'query': query,
                        'content': result.generated_response,
                        'sources': [doc.source for doc in result.retrieved_documents],
                        'confidence': result.confidence_score,
                        'relevance_scores': [doc.relevance_score for doc in result.retrieved_documents],
                        'timestamp': time.time()
                    }
                except Exception as e:
                    logger.error(f"Error executing query '{query}': {e}")
                    return None
        
        # Execute all queries
        query_tasks = [execute_query(query) for query in research_queries]
        query_results = await asyncio.gather(*query_tasks, return_exceptions=True)
        
        # Filter successful results
        for result in query_results:
            if isinstance(result, dict) and result is not None:
                findings.append(result)
        
        logger.info(f"Gathered {len(findings)} findings from {len(research_queries)} queries")
        return findings
    
    async def _generate_research_queries(self, main_query: str, research_type: ResearchType, 
                                       num_queries: int) -> List[str]:
        """Generate targeted research queries."""
        
        # Base query variations
        query_templates = {
            ResearchType.LITERATURE_REVIEW: [
                "What is {topic}?",
                "Overview of {topic}",
                "Current research on {topic}",
                "Key concepts in {topic}",
                "History and development of {topic}",
                "Applications of {topic}",
                "Challenges in {topic}",
                "Future directions for {topic}"
            ],
            ResearchType.COMPARATIVE_ANALYSIS: [
                "Compare {topic} alternatives",
                "Advantages and disadvantages of {topic}",
                "Different approaches to {topic}",
                "Evaluation criteria for {topic}",
                "{topic} vs competitors",
                "Strengths and weaknesses of {topic}",
                "Performance comparison {topic}",
                "Cost-benefit analysis {topic}"
            ],
            ResearchType.TECHNICAL_INVESTIGATION: [
                "How does {topic} work?",
                "Technical architecture of {topic}",
                "Implementation details {topic}",
                "System requirements for {topic}",
                "Technical specifications {topic}",
                "Performance characteristics {topic}",
                "Security considerations {topic}",
                "Scalability of {topic}"
            ],
            ResearchType.TREND_ANALYSIS: [
                "Trends in {topic}",
                "Future of {topic}",
                "Emerging developments in {topic}",
                "Market forecast for {topic}",
                "Evolution of {topic}",
                "Predictions about {topic}",
                "Growth patterns in {topic}",
                "Industry outlook for {topic}"
            ],
            ResearchType.PROBLEM_SOLVING: [
                "How to solve {topic}?",
                "Solutions for {topic}",
                "Best practices for {topic}",
                "Common problems with {topic}",
                "Troubleshooting {topic}",
                "Optimization strategies for {topic}",
                "Error resolution in {topic}",
                "Performance improvement {topic}"
            ],
            ResearchType.DATA_SYNTHESIS: [
                "Data analysis of {topic}",
                "Statistical insights on {topic}",
                "Research findings about {topic}",
                "Meta-analysis of {topic}",
                "Quantitative data on {topic}",
                "Survey results for {topic}",
                "Empirical evidence for {topic}",
                "Case studies of {topic}"
            ]
        }
        
        templates = query_templates[research_type]
        
        # Extract key topic from main query
        topic = self._extract_topic(main_query)
        
        # Generate queries
        queries = []
        for i, template in enumerate(templates[:num_queries]):
            query = template.format(topic=topic)
            queries.append(query)
        
        # Add the original query
        if main_query not in queries:
            queries.insert(0, main_query)
        
        return queries[:num_queries]
    
    def _extract_topic(self, query: str) -> str:
        """Extract main topic from query."""
        # Simple topic extraction - in practice, this could use NLP
        # Remove question words and common phrases
        stop_words = ['what', 'how', 'why', 'when', 'where', 'who', 'is', 'are', 'the', 'a', 'an']
        words = query.lower().split()
        topic_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Take first few meaningful words
        return ' '.join(topic_words[:3])
    
    async def _analyze_findings(self, research_task: ResearchTask, 
                              findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze and structure research findings."""
        logger.info(f"Analyzing findings for task {research_task.task_id}")
        
        # Update status
        if research_task.task_id in self.active_research:
            self.active_research[research_task.task_id]['status'] = ResearchStatus.ANALYZING
        
        analyzed_findings = []
        
        for finding in findings:
            try:
                # Use speculative decoder for analysis
                analysis_prompt = f"""
Analyze the following research finding and extract key insights:

Query: {finding['query']}
Content: {finding['content']}

Please provide:
1. Key insights
2. Important facts
3. Relevance to the main research question: {research_task.query}
4. Quality assessment
5. Potential limitations

Analysis:
"""
                
                decoding_request = DecodingRequest(
                    prompt=analysis_prompt,
                    max_tokens=300,
                    temperature=0.3,
                    strategy=SpeculationStrategy.TREE_ATTENTION
                )
                
                analysis_result = await self.speculative_decoder.decode(decoding_request)
                
                analyzed_finding = {
                    'original_finding': finding,
                    'analysis': analysis_result.text,
                    'key_insights': self._extract_insights(analysis_result.text),
                    'relevance_score': self._calculate_relevance(finding, research_task.query),
                    'quality_score': self._assess_quality(finding),
                    'analysis_confidence': analysis_result.confidence_scores
                }
                
                analyzed_findings.append(analyzed_finding)
                
            except Exception as e:
                logger.error(f"Error analyzing finding: {e}")
                # Include original finding even if analysis fails
                analyzed_findings.append({
                    'original_finding': finding,
                    'analysis': f"Analysis failed: {str(e)}",
                    'key_insights': [],
                    'relevance_score': 0.5,
                    'quality_score': 0.3,
                    'analysis_confidence': []
                })
        
        # Sort by relevance and quality
        analyzed_findings.sort(key=lambda x: x['relevance_score'] * x['quality_score'], reverse=True)
        
        logger.info(f"Analyzed {len(analyzed_findings)} findings")
        return analyzed_findings
    
    def _extract_insights(self, analysis_text: str) -> List[str]:
        """Extract key insights from analysis text."""
        insights = []
        
        # Look for numbered lists or bullet points
        lines = analysis_text.split('\n')
        for line in lines:
            line = line.strip()
            if re.match(r'^\d+\.', line) or line.startswith('•') or line.startswith('-'):
                insight = re.sub(r'^\d+\.\s*|^[•-]\s*', '', line)
                if len(insight) > 10:  # Filter out very short insights
                    insights.append(insight)
        
        return insights[:5]  # Limit to top 5 insights
    
    def _calculate_relevance(self, finding: Dict[str, Any], main_query: str) -> float:
        """Calculate relevance score of finding to main query."""
        # Simple relevance calculation based on keyword overlap
        main_words = set(main_query.lower().split())
        finding_words = set(finding['content'].lower().split())
        
        overlap = len(main_words.intersection(finding_words))
        union = len(main_words.union(finding_words))
        
        jaccard_similarity = overlap / union if union > 0 else 0
        
        # Combine with existing confidence
        base_confidence = finding.get('confidence', 0.5)
        
        return (jaccard_similarity + base_confidence) / 2
    
    def _assess_quality(self, finding: Dict[str, Any]) -> float:
        """Assess quality of a research finding."""
        quality_score = 0.5  # Base score
        
        # Content length (not too short, not too long)
        content_length = len(finding['content'])
        if 100 <= content_length <= 2000:
            quality_score += 0.2
        elif content_length < 50:
            quality_score -= 0.2
        
        # Source diversity
        sources = finding.get('sources', [])
        if len(sources) > 1:
            quality_score += 0.1
        
        # Confidence scores
        if finding.get('confidence', 0) > 0.7:
            quality_score += 0.2
        
        return min(1.0, max(0.0, quality_score))
    
    async def _synthesize_research(self, research_task: ResearchTask, 
                                 analyzed_findings: List[Dict[str, Any]]) -> str:
        """Synthesize research findings into comprehensive result."""
        logger.info(f"Synthesizing research for task {research_task.task_id}")
        
        # Update status
        if research_task.task_id in self.active_research:
            self.active_research[research_task.task_id]['status'] = ResearchStatus.SYNTHESIZING
        
        # Get synthesis template
        template = self.synthesis_templates[research_task.research_type]
        
        # Extract key information for synthesis
        all_insights = []
        all_sources = set()
        
        for finding in analyzed_findings:
            all_insights.extend(finding['key_insights'])
            all_sources.update(finding['original_finding'].get('sources', []))
        
        # Create synthesis prompt
        synthesis_prompt = f"""
Based on the following research findings, create a comprehensive synthesis for the query: {research_task.query}

Research Type: {research_task.research_type.value}
Depth Level: {research_task.depth_level}

Key Insights:
{chr(10).join([f"- {insight}" for insight in all_insights[:20]])}

Findings Summary:
{chr(10).join([f"Finding {i+1}: {finding['analysis'][:200]}..." for i, finding in enumerate(analyzed_findings[:5])])}

Please provide a comprehensive synthesis following this structure:
{template}

Synthesis:
"""
        
        try:
            decoding_request = DecodingRequest(
                prompt=synthesis_prompt,
                max_tokens=1000,
                temperature=0.4,
                strategy=SpeculationStrategy.QUANTUM_INSPIRED
            )
            
            synthesis_result = await self.speculative_decoder.decode(decoding_request)
            
            # Format the synthesis with template
            formatted_synthesis = self._format_synthesis(
                synthesis_result.text,
                research_task,
                all_sources
            )
            
            return formatted_synthesis
            
        except Exception as e:
            logger.error(f"Error in synthesis: {e}")
            return f"Synthesis failed: {str(e)}"
    
    def _format_synthesis(self, synthesis_text: str, research_task: ResearchTask, 
                         sources: set) -> str:
        """Format synthesis with proper structure."""
        template = self.synthesis_templates[research_task.research_type]
        
        # Extract topic from query
        topic = self._extract_topic(research_task.query)
        
        # Format sources
        sources_list = '\n'.join([f"- {source}" for source in sorted(sources)[:10]])
        
        # Basic template formatting
        formatted = template.format(
            topic=topic,
            overview=synthesis_text[:500] + "...",
            key_findings=synthesis_text,
            analysis=synthesis_text,
            conclusions=synthesis_text[-300:] if len(synthesis_text) > 300 else synthesis_text,
            sources=sources_list,
            framework=synthesis_text,
            differences=synthesis_text,
            similarities=synthesis_text,
            evaluation=synthesis_text,
            recommendations=synthesis_text,
            problem=research_task.query,
            technical_analysis=synthesis_text,
            solutions=synthesis_text,
            implementation=synthesis_text,
            conclusion=synthesis_text,
            references=sources_list,
            current_state=synthesis_text,
            historical_context=synthesis_text,
            trends=synthesis_text,
            projections=synthesis_text,
            implications=synthesis_text,
            problem_definition=research_task.query,
            root_causes=synthesis_text,
            recommendation=synthesis_text,
            risks=synthesis_text,
            data_sources=sources_list,
            methodology=synthesis_text,
            insights=synthesis_text,
            patterns=synthesis_text,
            synthesis=synthesis_text,
            limitations=synthesis_text
        )
        
        return formatted
    
    def _calculate_confidence_score(self, analyzed_findings: List[Dict[str, Any]], 
                                  synthesis: str) -> float:
        """Calculate overall confidence score for research result."""
        if not analyzed_findings:
            return 0.0
        
        # Average quality and relevance scores
        avg_quality = sum(f['quality_score'] for f in analyzed_findings) / len(analyzed_findings)
        avg_relevance = sum(f['relevance_score'] for f in analyzed_findings) / len(analyzed_findings)
        
        # Number of findings factor
        findings_factor = min(1.0, len(analyzed_findings) / 5.0)
        
        # Synthesis length factor (reasonable length indicates good synthesis)
        synthesis_factor = min(1.0, len(synthesis) / 1000.0)
        
        # Combine factors
        confidence = (avg_quality * 0.3 + avg_relevance * 0.3 + 
                     findings_factor * 0.2 + synthesis_factor * 0.2)
        
        return min(1.0, max(0.0, confidence))
    
    def _extract_sources(self, analyzed_findings: List[Dict[str, Any]]) -> List[str]:
        """Extract all sources from analyzed findings."""
        sources = set()
        for finding in analyzed_findings:
            sources.update(finding['original_finding'].get('sources', []))
        return list(sources)
    
    def _generate_task_id(self, query: str) -> str:
        """Generate unique task ID."""
        content = f"{query}_{time.time()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _update_metrics(self, research_result: ResearchResult):
        """Update performance metrics."""
        self.metrics['total_research_tasks'] += 1
        self.metrics['research_by_type'][research_result.research_type.value] += 1
        
        if research_result.status == ResearchStatus.COMPLETED:
            self.metrics['completed_tasks'] += 1
            
            # Update averages
            total_completed = self.metrics['completed_tasks']
            
            # Processing time
            total_time = (self.metrics['average_processing_time'] * (total_completed - 1) + 
                         research_result.processing_time)
            self.metrics['average_processing_time'] = total_time / total_completed
            
            # Confidence score
            total_confidence = (self.metrics['average_confidence_score'] * (total_completed - 1) + 
                              research_result.confidence_score)
            self.metrics['average_confidence_score'] = total_confidence / total_completed
        
        # Success rate
        self.metrics['success_rate'] = self.metrics['completed_tasks'] / self.metrics['total_research_tasks']
    
    async def _research_processing_loop(self):
        """Background loop for processing queued research tasks."""
        while self.is_running:
            try:
                # Process any queued research tasks
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in research processing loop: {e}")
                await asyncio.sleep(1)
    
    async def _metrics_collection_loop(self):
        """Background loop for metrics collection."""
        while self.is_running:
            try:
                if self.metrics['total_research_tasks'] > 0:
                    logger.info(f"Research Agent Metrics - "
                              f"Total Tasks: {self.metrics['total_research_tasks']}, "
                              f"Success Rate: {self.metrics['success_rate']:.2%}, "
                              f"Avg Processing Time: {self.metrics['average_processing_time']:.2f}s, "
                              f"Avg Confidence: {self.metrics['average_confidence_score']:.3f}")
                
                await asyncio.sleep(300)  # Log every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(300)
    
    async def _knowledge_update_loop(self):
        """Background loop for updating knowledge base."""
        while self.is_running:
            try:
                # Update research knowledge base with new findings
                await asyncio.sleep(3600)  # Update every hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in knowledge update: {e}")
                await asyncio.sleep(3600)
    
    async def _quality_assessment_loop(self):
        """Background loop for assessing research quality."""
        while self.is_running:
            try:
                # Assess quality of completed research
                await asyncio.sleep(1800)  # Assess every 30 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in quality assessment: {e}")
                await asyncio.sleep(1800)
    
    async def _initialize_research_kb(self):
        """Initialize research knowledge base."""
        try:
            # Initialize research knowledge base with common domains
            self.research_kb = {
                'technology': {
                    'sources': ['tech_docs', 'api_references', 'technical_papers'],
                    'keywords': ['software', 'hardware', 'programming', 'algorithm', 'system'],
                    'quality_indicators': ['peer-reviewed', 'official documentation', 'established source']
                },
                'business': {
                    'sources': ['business_reports', 'market_analysis', 'case_studies'],
                    'keywords': ['market', 'strategy', 'revenue', 'growth', 'analysis'],
                    'quality_indicators': ['authoritative source', 'recent data', 'verified statistics']
                },
                'science': {
                    'sources': ['research_papers', 'journals', 'academic_sources'],
                    'keywords': ['research', 'study', 'experiment', 'hypothesis', 'data'],
                    'quality_indicators': ['peer-reviewed', 'citations', 'methodology']
                },
                'general': {
                    'sources': ['encyclopedias', 'reference_materials', 'verified_sources'],
                    'keywords': ['information', 'facts', 'overview', 'explanation'],
                    'quality_indicators': ['credible source', 'factual accuracy', 'comprehensive']
                }
            }
            
            # Load domain-specific research patterns
            kb_file = self.config.data_dir / "research_kb.json"
            if kb_file.exists():
                with open(kb_file, 'r') as f:
                    saved_kb = json.load(f)
                    self.research_kb.update(saved_kb)
                    
            logger.info(f"Initialized research knowledge base with {len(self.research_kb)} domains")
            
        except Exception as e:
            logger.error(f"Error initializing research knowledge base: {e}")
            self.research_kb = {}
    
    async def _load_research_templates(self):
        """Load research templates from storage."""
        try:
            # Initialize research templates for different types of research
            self.research_templates = {
                'technical_analysis': {
                    'structure': [
                        'Problem Definition',
                        'Technical Background',
                        'Current Solutions',
                        'Analysis and Comparison',
                        'Recommendations',
                        'Implementation Considerations'
                    ],
                    'questions': [
                        'What is the core technical problem?',
                        'What are the existing approaches?',
                        'What are the trade-offs?',
                        'What is the recommended solution?'
                    ]
                },
                'market_research': {
                    'structure': [
                        'Market Overview',
                        'Key Players',
                        'Market Trends',
                        'Opportunities and Challenges',
                        'Competitive Analysis',
                        'Market Projections'
                    ],
                    'questions': [
                        'What is the market size?',
                        'Who are the main competitors?',
                        'What are the growth trends?',
                        'What opportunities exist?'
                    ]
                },
                'academic_research': {
                    'structure': [
                        'Literature Review',
                        'Methodology',
                        'Key Findings',
                        'Analysis and Discussion',
                        'Conclusions',
                        'Future Research Directions'
                    ],
                    'questions': [
                        'What does existing research show?',
                        'What methodologies were used?',
                        'What are the key findings?',
                        'What are the implications?'
                    ]
                },
                'general_inquiry': {
                    'structure': [
                        'Background Information',
                        'Key Facts and Data',
                        'Different Perspectives',
                        'Analysis and Synthesis',
                        'Summary and Conclusions'
                    ],
                    'questions': [
                        'What are the basic facts?',
                        'What are different viewpoints?',
                        'What is the overall picture?',
                        'What conclusions can be drawn?'
                    ]
                }
            }
            
            # Load custom templates if available
            templates_file = self.config.data_dir / "research_templates.json"
            if templates_file.exists():
                with open(templates_file, 'r') as f:
                    custom_templates = json.load(f)
                    self.research_templates.update(custom_templates)
                    
            logger.info(f"Loaded {len(self.research_templates)} research templates")
            
        except Exception as e:
            logger.error(f"Error loading research templates: {e}")
            self.research_templates = {}
    
    async def _save_research_results(self):
        """Save research results to persistent storage."""
        try:
            # Save recent research results for future reference
            if not hasattr(self, 'research_history') or not self.research_history:
                return
                
            results_file = self.config.data_dir / "research_results.json"
            
            # Keep only recent results (last 100)
            recent_results = list(self.research_history)[-100:]
            
            # Prepare data for saving (remove large content to save space)
            save_data = []
            for result in recent_results:
                save_item = {
                    'query': result.get('query', ''),
                    'timestamp': result.get('timestamp', time.time()),
                    'research_type': result.get('research_type', 'general'),
                    'sources_count': len(result.get('sources', [])),
                    'findings_count': len(result.get('findings', [])),
                    'confidence': result.get('confidence', 0),
                    'summary': result.get('summary', '')[:500]  # Truncate summary
                }
                save_data.append(save_item)
            
            with open(results_file, 'w') as f:
                json.dump(save_data, f, indent=2)
                
            logger.info(f"Saved {len(save_data)} research results to storage")
            
        except Exception as e:
            logger.error(f"Error saving research results: {e}")
    
    # Public API methods
    
    async def health_check(self) -> str:
        """Perform health check."""
        try:
            # Test basic research functionality
            test_result = await self.conduct_research(
                "What is artificial intelligence?",
                ResearchType.LITERATURE_REVIEW,
                depth_level=1,
                time_limit=30.0
            )
            
            if test_result.status == ResearchStatus.COMPLETED:
                return "healthy"
            else:
                return "unhealthy"
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return "unhealthy"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get research agent statistics."""
        return {
            'metrics': self.metrics.copy(),
            'active_research': len(self.active_research),
            'completed_research': len(self.completed_research)
        }
    
    def get_research_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a research task."""
        if task_id in self.completed_research:
            result = self.completed_research[task_id]
            return {
                'task_id': task_id,
                'status': result.status.value,
                'processing_time': result.processing_time,
                'confidence_score': result.confidence_score,
                'findings_count': len(result.findings)
            }
        elif task_id in self.active_research:
            research = self.active_research[task_id]
            return {
                'task_id': task_id,
                'status': research['status'].value,
                'processing_time': time.time() - research['start_time'],
                'findings_count': len(research['findings'])
            }
        else:
            return None
    
    async def restart(self):
        """Restart the research agent."""
        logger.info("Restarting Research Agent...")
        await self.shutdown()
        await asyncio.sleep(1)
        await self.initialize()
        await self.start()