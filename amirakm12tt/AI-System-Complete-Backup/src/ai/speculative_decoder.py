"""
Quantum-Inspired Speculative Decoder
Advanced language model inference optimization using speculative execution
"""

import asyncio
import logging
import time
import random
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForCausalLM
import openai
from concurrent.futures import ThreadPoolExecutor
import threading

from ..core.config import SystemConfig

logger = logging.getLogger(__name__)

class SpeculationStrategy(Enum):
    """Strategies for speculative decoding."""
    DRAFT_TARGET = "draft_target"
    PARALLEL_SAMPLING = "parallel_sampling"
    TREE_ATTENTION = "tree_attention"
    QUANTUM_INSPIRED = "quantum_inspired"

@dataclass
class SpeculationResult:
    """Result from speculative decoding."""
    tokens: List[int]
    text: str
    confidence_scores: List[float]
    acceptance_rate: float
    speculation_depth: int
    processing_time: float
    strategy_used: str
    metadata: Dict[str, Any]

@dataclass
class DecodingRequest:
    """Request for speculative decoding."""
    prompt: str
    max_tokens: int = 100
    temperature: float = 0.7
    top_p: float = 0.9
    speculation_length: int = 5
    strategy: SpeculationStrategy = SpeculationStrategy.DRAFT_TARGET
    metadata: Dict[str, Any] = None

class QuantumInspiredSpeculator:
    """Quantum-inspired speculation mechanism."""
    
    def __init__(self, vocab_size: int, hidden_dim: int = 256):
        self.vocab_size = vocab_size
        self.hidden_dim = hidden_dim
        
        # Quantum-inspired parameters
        self.superposition_weights = np.random.normal(0, 0.1, (vocab_size, hidden_dim))
        self.entanglement_matrix = np.random.orthogonal(hidden_dim)
        self.measurement_basis = np.random.orthogonal(hidden_dim)
        
        # Adaptation parameters
        self.learning_rate = 0.01
        self.success_history = []
        
    def speculate(self, context_embedding: np.ndarray, num_tokens: int) -> List[Tuple[int, float]]:
        """Generate speculative tokens using quantum-inspired approach."""
        speculated_tokens = []
        current_state = context_embedding.copy()
        
        for _ in range(num_tokens):
            # Apply superposition
            superposed_state = np.dot(current_state, self.superposition_weights.T)
            
            # Apply entanglement
            entangled_state = np.dot(superposed_state, self.entanglement_matrix)
            
            # Measurement (collapse to token probabilities)
            measured_state = np.dot(entangled_state, self.measurement_basis.T)
            probabilities = F.softmax(torch.tensor(measured_state), dim=-1).numpy()
            
            # Sample token
            token_id = np.random.choice(self.vocab_size, p=probabilities)
            confidence = probabilities[token_id]
            
            speculated_tokens.append((token_id, confidence))
            
            # Update state for next iteration
            current_state = self._update_quantum_state(current_state, token_id)
        
        return speculated_tokens
    
    def _update_quantum_state(self, state: np.ndarray, token_id: int) -> np.ndarray:
        """Update quantum state based on selected token."""
        # Simple state evolution (in practice, this would be more sophisticated)
        token_embedding = self.superposition_weights[token_id]
        updated_state = 0.7 * state + 0.3 * token_embedding
        return updated_state / np.linalg.norm(updated_state)
    
    def adapt(self, success_rate: float):
        """Adapt quantum parameters based on success rate."""
        self.success_history.append(success_rate)
        
        if len(self.success_history) > 10:
            recent_performance = np.mean(self.success_history[-10:])
            
            # Adjust parameters based on performance
            if recent_performance < 0.5:
                # Increase exploration
                noise = np.random.normal(0, 0.05, self.superposition_weights.shape)
                self.superposition_weights += noise
            elif recent_performance > 0.8:
                # Reduce exploration, increase exploitation
                self.superposition_weights *= 0.99

class TreeAttentionSpeculator:
    """Tree-based attention speculation mechanism."""
    
    def __init__(self, max_depth: int = 3, branching_factor: int = 3):
        self.max_depth = max_depth
        self.branching_factor = branching_factor
        self.tree_cache = {}
        
    def speculate_tree(self, context: str, tokenizer, model, depth: int = 0) -> Dict[str, Any]:
        """Generate speculation tree."""
        if depth >= self.max_depth:
            return {'tokens': [], 'children': {}}
        
        # Check cache
        cache_key = f"{hash(context)}_{depth}"
        if cache_key in self.tree_cache:
            return self.tree_cache[cache_key]
        
        # Generate top-k candidates
        inputs = tokenizer.encode(context, return_tensors="pt")
        with torch.no_grad():
            outputs = model(inputs)
            logits = outputs.logits[0, -1, :]
            top_k_tokens = torch.topk(logits, self.branching_factor)
        
        tree_node = {'tokens': [], 'children': {}}
        
        for i, (score, token_id) in enumerate(zip(top_k_tokens.values, top_k_tokens.indices)):
            token = tokenizer.decode([token_id])
            new_context = context + token
            
            # Recursively build subtree
            subtree = self.speculate_tree(new_context, tokenizer, model, depth + 1)
            
            tree_node['children'][token] = {
                'token_id': token_id.item(),
                'score': score.item(),
                'subtree': subtree
            }
        
        # Cache result
        self.tree_cache[cache_key] = tree_node
        return tree_node
    
    def traverse_tree(self, tree: Dict[str, Any], max_tokens: int) -> List[Tuple[int, float]]:
        """Traverse tree to find best path."""
        path = []
        current_node = tree
        
        for _ in range(max_tokens):
            if not current_node.get('children'):
                break
            
            # Select best child based on score
            best_child = max(
                current_node['children'].items(),
                key=lambda x: x[1]['score']
            )
            
            token_name, child_info = best_child
            path.append((child_info['token_id'], child_info['score']))
            current_node = child_info['subtree']
        
        return path

class SpeculativeDecoder:
    """Main speculative decoder class."""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.is_running = False
        
        # Models
        self.draft_model = None
        self.target_model = None
        self.tokenizer = None
        
        # Speculation mechanisms
        self.quantum_speculator = None
        self.tree_speculator = None
        
        # Performance tracking
        self.metrics = {
            'total_requests': 0,
            'total_tokens_generated': 0,
            'total_tokens_accepted': 0,
            'average_acceptance_rate': 0.0,
            'processing_times': [],
            'strategy_performance': {}
        }
        
        # Threading
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
        logger.info("Speculative Decoder initialized")
    
    async def initialize(self):
        """Initialize the speculative decoder."""
        logger.info("Initializing Speculative Decoder...")
        
        try:
            # Initialize models
            await self._initialize_models()
            
            # Initialize speculation mechanisms
            await self._initialize_speculators()
            
            # Initialize OpenAI client if available
            self._initialize_openai()
            
            logger.info("Speculative Decoder initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Speculative Decoder: {e}")
            raise
    
    async def start(self):
        """Start the speculative decoder."""
        logger.info("Starting Speculative Decoder...")
        
        try:
            # Start background tasks
            self.background_tasks = {
                'performance_monitor': asyncio.create_task(self._performance_monitoring_loop()),
                'model_optimizer': asyncio.create_task(self._model_optimization_loop()),
                'cache_manager': asyncio.create_task(self._cache_management_loop())
            }
            
            self.is_running = True
            logger.info("Speculative Decoder started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Speculative Decoder: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the speculative decoder."""
        logger.info("Shutting down Speculative Decoder...")
        
        self.is_running = False
        
        # Cancel background tasks
        for task_name, task in self.background_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Cancelled {task_name}")
        
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)
        
        logger.info("Speculative Decoder shutdown complete")
    
    async def _initialize_models(self):
        """Initialize draft and target models."""
        draft_model_name = self.config.speculative_decoding.draft_model
        target_model_name = self.config.speculative_decoding.target_model
        
        try:
            # Load models in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            # Load tokenizer
            self.tokenizer = await loop.run_in_executor(
                self.thread_pool,
                AutoTokenizer.from_pretrained,
                draft_model_name
            )
            
            # Load draft model (smaller, faster)
            self.draft_model = await loop.run_in_executor(
                self.thread_pool,
                AutoModelForCausalLM.from_pretrained,
                draft_model_name
            )
            
            # Load target model (larger, more accurate) - optional
            try:
                self.target_model = await loop.run_in_executor(
                    self.thread_pool,
                    AutoModelForCausalLM.from_pretrained,
                    target_model_name
                )
                logger.info(f"Loaded target model: {target_model_name}")
            except Exception as e:
                logger.warning(f"Could not load target model: {e}")
                self.target_model = None
            
            # Set models to evaluation mode
            self.draft_model.eval()
            if self.target_model:
                self.target_model.eval()
            
            logger.info(f"Loaded draft model: {draft_model_name}")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise
    
    async def _initialize_speculators(self):
        """Initialize speculation mechanisms."""
        vocab_size = len(self.tokenizer.vocab) if self.tokenizer else 50000
        
        # Initialize quantum-inspired speculator
        self.quantum_speculator = QuantumInspiredSpeculator(vocab_size)
        
        # Initialize tree attention speculator
        self.tree_speculator = TreeAttentionSpeculator()
        
        logger.info("Speculation mechanisms initialized")
    
    def _initialize_openai(self):
        """Initialize OpenAI client."""
        api_key = self.config.get_api_key("openai")
        if api_key:
            openai.api_key = api_key
            logger.info("OpenAI client initialized for speculative decoding")
    
    async def decode(self, request: Union[str, DecodingRequest]) -> SpeculationResult:
        """Perform speculative decoding."""
        start_time = time.time()
        
        # Convert string to DecodingRequest if needed
        if isinstance(request, str):
            request = DecodingRequest(prompt=request)
        
        try:
            # Choose decoding strategy
            if request.strategy == SpeculationStrategy.DRAFT_TARGET and self.target_model:
                result = await self._draft_target_decode(request)
            elif request.strategy == SpeculationStrategy.PARALLEL_SAMPLING:
                result = await self._parallel_sampling_decode(request)
            elif request.strategy == SpeculationStrategy.TREE_ATTENTION:
                result = await self._tree_attention_decode(request)
            elif request.strategy == SpeculationStrategy.QUANTUM_INSPIRED:
                result = await self._quantum_inspired_decode(request)
            else:
                # Fallback to standard decoding
                result = await self._standard_decode(request)
            
            # Update metrics
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            
            self._update_metrics(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in speculative decoding: {e}")
            # Return fallback result
            return SpeculationResult(
                tokens=[],
                text="Error in decoding",
                confidence_scores=[],
                acceptance_rate=0.0,
                speculation_depth=0,
                processing_time=time.time() - start_time,
                strategy_used="error",
                metadata={'error': str(e)}
            )
    
    async def _draft_target_decode(self, request: DecodingRequest) -> SpeculationResult:
        """Draft-target speculative decoding."""
        if not self.target_model:
            return await self._standard_decode(request)
        
        loop = asyncio.get_event_loop()
        
        # Tokenize prompt
        inputs = self.tokenizer.encode(request.prompt, return_tensors="pt")
        generated_tokens = inputs[0].tolist()
        confidence_scores = []
        accepted_tokens = 0
        total_speculated = 0
        
        while len(generated_tokens) - len(inputs[0]) < request.max_tokens:
            # Generate draft sequence
            draft_tokens = await loop.run_in_executor(
                self.thread_pool,
                self._generate_draft_sequence,
                torch.tensor([generated_tokens]),
                request.speculation_length,
                request.temperature
            )
            
            # Verify with target model
            verification_result = await loop.run_in_executor(
                self.thread_pool,
                self._verify_with_target,
                torch.tensor([generated_tokens + draft_tokens]),
                draft_tokens,
                request.temperature
            )
            
            accepted_tokens += verification_result['accepted_count']
            total_speculated += len(draft_tokens)
            
            generated_tokens.extend(verification_result['accepted_tokens'])
            confidence_scores.extend(verification_result['confidence_scores'])
            
            # Break if we've generated enough tokens
            if len(generated_tokens) - len(inputs[0]) >= request.max_tokens:
                break
        
        # Decode tokens to text
        generated_text = self.tokenizer.decode(
            generated_tokens[len(inputs[0]):],
            skip_special_tokens=True
        )
        
        acceptance_rate = accepted_tokens / total_speculated if total_speculated > 0 else 0.0
        
        return SpeculationResult(
            tokens=generated_tokens[len(inputs[0]):],
            text=generated_text,
            confidence_scores=confidence_scores,
            acceptance_rate=acceptance_rate,
            speculation_depth=request.speculation_length,
            processing_time=0.0,  # Will be set by caller
            strategy_used="draft_target",
            metadata={
                'total_speculated': total_speculated,
                'accepted_tokens': accepted_tokens
            }
        )
    
    async def _parallel_sampling_decode(self, request: DecodingRequest) -> SpeculationResult:
        """Parallel sampling speculative decoding."""
        loop = asyncio.get_event_loop()
        
        # Generate multiple parallel sequences
        num_parallel = 3
        tasks = []
        
        for _ in range(num_parallel):
            task = loop.run_in_executor(
                self.thread_pool,
                self._generate_single_sequence,
                request.prompt,
                request.max_tokens,
                request.temperature + random.uniform(-0.1, 0.1)  # Slight temperature variation
            )
            tasks.append(task)
        
        # Wait for all sequences
        sequences = await asyncio.gather(*tasks)
        
        # Select best sequence based on perplexity or other criteria
        best_sequence = min(sequences, key=lambda x: x.get('perplexity', float('inf')))
        
        return SpeculationResult(
            tokens=best_sequence['tokens'],
            text=best_sequence['text'],
            confidence_scores=best_sequence['confidence_scores'],
            acceptance_rate=1.0,  # All tokens from best sequence are "accepted"
            speculation_depth=num_parallel,
            processing_time=0.0,
            strategy_used="parallel_sampling",
            metadata={
                'num_sequences': num_parallel,
                'best_perplexity': best_sequence.get('perplexity', 0.0)
            }
        )
    
    async def _tree_attention_decode(self, request: DecodingRequest) -> SpeculationResult:
        """Tree attention speculative decoding."""
        loop = asyncio.get_event_loop()
        
        # Build speculation tree
        tree = await loop.run_in_executor(
            self.thread_pool,
            self.tree_speculator.speculate_tree,
            request.prompt,
            self.tokenizer,
            self.draft_model
        )
        
        # Traverse tree to get best path
        best_path = self.tree_speculator.traverse_tree(tree, request.max_tokens)
        
        # Extract tokens and scores
        tokens = [token_id for token_id, _ in best_path]
        confidence_scores = [score for _, score in best_path]
        
        # Decode to text
        text = self.tokenizer.decode(tokens, skip_special_tokens=True)
        
        return SpeculationResult(
            tokens=tokens,
            text=text,
            confidence_scores=confidence_scores,
            acceptance_rate=1.0,  # Tree traversal accepts all tokens in path
            speculation_depth=self.tree_speculator.max_depth,
            processing_time=0.0,
            strategy_used="tree_attention",
            metadata={
                'tree_depth': self.tree_speculator.max_depth,
                'branching_factor': self.tree_speculator.branching_factor
            }
        )
    
    async def _quantum_inspired_decode(self, request: DecodingRequest) -> SpeculationResult:
        """Quantum-inspired speculative decoding."""
        loop = asyncio.get_event_loop()
        
        # Get context embedding
        inputs = self.tokenizer.encode(request.prompt, return_tensors="pt")
        with torch.no_grad():
            outputs = self.draft_model(inputs, output_hidden_states=True)
            context_embedding = outputs.hidden_states[-1][0, -1, :].numpy()
        
        # Generate speculative tokens using quantum approach
        speculated_tokens = await loop.run_in_executor(
            self.thread_pool,
            self.quantum_speculator.speculate,
            context_embedding,
            request.max_tokens
        )
        
        # Extract tokens and confidence scores
        tokens = [token_id for token_id, _ in speculated_tokens]
        confidence_scores = [confidence for _, confidence in speculated_tokens]
        
        # Decode to text
        text = self.tokenizer.decode(tokens, skip_special_tokens=True)
        
        # Calculate acceptance rate (simulate verification)
        acceptance_rate = np.mean(confidence_scores)
        
        # Adapt quantum parameters
        self.quantum_speculator.adapt(acceptance_rate)
        
        return SpeculationResult(
            tokens=tokens,
            text=text,
            confidence_scores=confidence_scores,
            acceptance_rate=acceptance_rate,
            speculation_depth=request.max_tokens,
            processing_time=0.0,
            strategy_used="quantum_inspired",
            metadata={
                'quantum_adaptation': acceptance_rate
            }
        )
    
    async def _standard_decode(self, request: DecodingRequest) -> SpeculationResult:
        """Standard (non-speculative) decoding as fallback."""
        loop = asyncio.get_event_loop()
        
        result = await loop.run_in_executor(
            self.thread_pool,
            self._generate_single_sequence,
            request.prompt,
            request.max_tokens,
            request.temperature
        )
        
        return SpeculationResult(
            tokens=result['tokens'],
            text=result['text'],
            confidence_scores=result['confidence_scores'],
            acceptance_rate=1.0,
            speculation_depth=1,
            processing_time=0.0,
            strategy_used="standard",
            metadata={}
        )
    
    def _generate_draft_sequence(self, inputs: torch.Tensor, length: int, temperature: float) -> List[int]:
        """Generate draft sequence using draft model."""
        generated_tokens = []
        current_inputs = inputs
        
        with torch.no_grad():
            for _ in range(length):
                outputs = self.draft_model(current_inputs)
                logits = outputs.logits[0, -1, :] / temperature
                probabilities = F.softmax(logits, dim=-1)
                
                # Sample next token
                next_token = torch.multinomial(probabilities, 1).item()
                generated_tokens.append(next_token)
                
                # Update inputs
                current_inputs = torch.cat([
                    current_inputs,
                    torch.tensor([[next_token]])
                ], dim=1)
        
        return generated_tokens
    
    def _verify_with_target(self, inputs: torch.Tensor, draft_tokens: List[int], temperature: float) -> Dict[str, Any]:
        """Verify draft tokens with target model."""
        accepted_tokens = []
        confidence_scores = []
        
        with torch.no_grad():
            # Get target model predictions
            outputs = self.target_model(inputs)
            logits = outputs.logits[0, -(len(draft_tokens)+1):-1, :]  # Get logits for draft positions
            
            for i, draft_token in enumerate(draft_tokens):
                # Get probability of draft token according to target model
                token_logits = logits[i] / temperature
                probabilities = F.softmax(token_logits, dim=-1)
                draft_prob = probabilities[draft_token].item()
                
                # Accept token based on probability threshold
                acceptance_threshold = self.config.speculative_decoding.acceptance_threshold
                if draft_prob >= acceptance_threshold:
                    accepted_tokens.append(draft_token)
                    confidence_scores.append(draft_prob)
                else:
                    # Reject token and resample from target distribution
                    new_token = torch.multinomial(probabilities, 1).item()
                    accepted_tokens.append(new_token)
                    confidence_scores.append(probabilities[new_token].item())
                    break  # Stop accepting further tokens
        
        return {
            'accepted_tokens': accepted_tokens,
            'accepted_count': len(accepted_tokens),
            'confidence_scores': confidence_scores
        }
    
    def _generate_single_sequence(self, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        """Generate a single sequence using the draft model."""
        inputs = self.tokenizer.encode(prompt, return_tensors="pt")
        generated_tokens = []
        confidence_scores = []
        
        with torch.no_grad():
            current_inputs = inputs
            
            for _ in range(max_tokens):
                outputs = self.draft_model(current_inputs)
                logits = outputs.logits[0, -1, :] / temperature
                probabilities = F.softmax(logits, dim=-1)
                
                # Sample next token
                next_token = torch.multinomial(probabilities, 1).item()
                confidence = probabilities[next_token].item()
                
                generated_tokens.append(next_token)
                confidence_scores.append(confidence)
                
                # Update inputs
                current_inputs = torch.cat([
                    current_inputs,
                    torch.tensor([[next_token]])
                ], dim=1)
                
                # Stop at end token
                if next_token == self.tokenizer.eos_token_id:
                    break
        
        # Decode to text
        text = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
        
        # Calculate perplexity (simplified)
        perplexity = np.exp(-np.mean(np.log(confidence_scores))) if confidence_scores else float('inf')
        
        return {
            'tokens': generated_tokens,
            'text': text,
            'confidence_scores': confidence_scores,
            'perplexity': perplexity
        }
    
    def _update_metrics(self, result: SpeculationResult):
        """Update performance metrics."""
        self.metrics['total_requests'] += 1
        self.metrics['total_tokens_generated'] += len(result.tokens)
        self.metrics['total_tokens_accepted'] += int(len(result.tokens) * result.acceptance_rate)
        
        # Update average acceptance rate
        total_acceptance = self.metrics['total_tokens_accepted']
        total_generated = self.metrics['total_tokens_generated']
        self.metrics['average_acceptance_rate'] = total_acceptance / total_generated if total_generated > 0 else 0.0
        
        # Track processing times
        self.metrics['processing_times'].append(result.processing_time)
        if len(self.metrics['processing_times']) > 1000:
            self.metrics['processing_times'] = self.metrics['processing_times'][-1000:]
        
        # Track strategy performance
        strategy = result.strategy_used
        if strategy not in self.metrics['strategy_performance']:
            self.metrics['strategy_performance'][strategy] = {
                'count': 0,
                'total_acceptance_rate': 0.0,
                'total_processing_time': 0.0
            }
        
        perf = self.metrics['strategy_performance'][strategy]
        perf['count'] += 1
        perf['total_acceptance_rate'] += result.acceptance_rate
        perf['total_processing_time'] += result.processing_time
    
    async def _performance_monitoring_loop(self):
        """Monitor and log performance metrics."""
        while self.is_running:
            try:
                if self.metrics['total_requests'] > 0:
                    avg_processing_time = np.mean(self.metrics['processing_times']) if self.metrics['processing_times'] else 0
                    
                    logger.info(f"Speculative Decoder Metrics - "
                              f"Requests: {self.metrics['total_requests']}, "
                              f"Avg Acceptance Rate: {self.metrics['average_acceptance_rate']:.3f}, "
                              f"Avg Processing Time: {avg_processing_time:.3f}s")
                    
                    # Log strategy performance
                    for strategy, perf in self.metrics['strategy_performance'].items():
                        if perf['count'] > 0:
                            avg_acceptance = perf['total_acceptance_rate'] / perf['count']
                            avg_time = perf['total_processing_time'] / perf['count']
                            logger.info(f"Strategy {strategy}: "
                                      f"Count: {perf['count']}, "
                                      f"Avg Acceptance: {avg_acceptance:.3f}, "
                                      f"Avg Time: {avg_time:.3f}s")
                
                await asyncio.sleep(300)  # Log every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                await asyncio.sleep(300)
    
    async def _model_optimization_loop(self):
        """Optimize models based on performance."""
        while self.is_running:
            try:
                # Perform model optimization (placeholder)
                # In practice, this could involve model pruning, quantization, etc.
                
                await asyncio.sleep(1800)  # Optimize every 30 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in model optimization: {e}")
                await asyncio.sleep(1800)
    
    async def _cache_management_loop(self):
        """Manage speculation caches."""
        while self.is_running:
            try:
                # Clean up tree speculation cache
                if hasattr(self.tree_speculator, 'tree_cache'):
                    cache_size = len(self.tree_speculator.tree_cache)
                    if cache_size > 1000:  # Limit cache size
                        # Remove oldest entries
                        keys_to_remove = list(self.tree_speculator.tree_cache.keys())[:cache_size//2]
                        for key in keys_to_remove:
                            del self.tree_speculator.tree_cache[key]
                        
                        logger.info(f"Cleaned speculation cache, removed {len(keys_to_remove)} entries")
                
                await asyncio.sleep(600)  # Clean every 10 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache management: {e}")
                await asyncio.sleep(600)
    
    # Public API methods
    
    async def health_check(self) -> str:
        """Perform health check."""
        try:
            # Test model inference
            test_request = DecodingRequest(
                prompt="Test",
                max_tokens=1,
                strategy=SpeculationStrategy.DRAFT_TARGET
            )
            
            result = await self.decode(test_request)
            
            if result.tokens:
                return "healthy"
            else:
                return "unhealthy"
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return "unhealthy"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get decoder statistics."""
        stats = self.metrics.copy()
        
        # Add derived statistics
        if stats['processing_times']:
            stats['avg_processing_time'] = np.mean(stats['processing_times'])
            stats['median_processing_time'] = np.median(stats['processing_times'])
        
        # Add strategy statistics
        for strategy, perf in stats['strategy_performance'].items():
            if perf['count'] > 0:
                stats['strategy_performance'][strategy]['avg_acceptance_rate'] = \
                    perf['total_acceptance_rate'] / perf['count']
                stats['strategy_performance'][strategy]['avg_processing_time'] = \
                    perf['total_processing_time'] / perf['count']
        
        return stats
    
    async def restart(self):
        """Restart the speculative decoder."""
        logger.info("Restarting Speculative Decoder...")
        await self.shutdown()
        await asyncio.sleep(1)
        await self.initialize()
        await self.start()