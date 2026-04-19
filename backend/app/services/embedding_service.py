"""
Embedding Service - Handles embeddings via OpenRouter API
Uses: nvidia/llama-nemotron-embed-vl-1b-v2:free
"""

import logging
import os
import requests
import json
import numpy as np
import time
from typing import List, Union
from functools import lru_cache
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using OpenRouter API"""
    
    def __init__(self, api_key: str = None, model: str = None):
        """
        Initialize embedding service
        Args:
            api_key: OpenRouter API key (defaults to env variable)
            model: Model name (defaults to env variable)
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model or os.getenv("OPENROUTER_EMBEDDING_MODEL", "nvidia/llama-nemotron-embed-vl-1b-v2:free")
        self.api_url = "https://openrouter.ai/api/v1/embeddings"
        self.embedding_dim = None  # Will be detected from first API call
        
        if not self.api_key:
            logger.error("OpenRouter API key not found in environment variables")
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        
        logger.info(f"Initialized EmbeddingService with model: {self.model}")
    
    def _detect_embedding_dim(self, embedding: np.ndarray):
        """Detect and store embedding dimension from first response"""
        if self.embedding_dim is None:
            self.embedding_dim = len(embedding)
            logger.info(f"Detected embedding dimension: {self.embedding_dim}")
    
    def embed_text(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Embed text using OpenRouter API
        Args:
            text: Single string or list of strings to embed
        Returns:
            numpy array of embeddings
        """
        if isinstance(text, str):
            texts = [text]
            single_input = True
        else:
            texts = text
            single_input = False
        
        try:
            # Prepare request
            payload = {
                "model": self.model,
                "input": [{"content": [{"type": "text", "text": t}]} for t in texts],
                "encoding_format": "float"
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
            logger.debug(f"Sending embedding request for {len(texts)} texts...")
            
            # Make request
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"OpenRouter API error: {response.status_code}")
                logger.error(f"Response: {response.text}")
                raise Exception(f"OpenRouter API error: {response.text}")
            
            # Parse response
            result = response.json()
            
            # Check for errors in response
            if "error" in result:
                logger.error(f"OpenRouter API error in response: {result['error']}")
                raise Exception(f"OpenRouter API error: {result['error']}")
            
            if "data" not in result:
                logger.error(f"Unexpected API response format: {result}")
                raise Exception(f"OpenRouter API response missing 'data' key. Response: {result}")
            
            embeddings = [np.array(item["embedding"]) for item in result["data"]]
            
            # Detect dimension from first embedding
            if embeddings:
                self._detect_embedding_dim(embeddings[0])
            
            # Return as numpy array
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            if single_input:
                return embeddings_array[0]
            else:
                return embeddings_array
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during embedding request: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def embed_batch(self, texts: List[str], batch_size: int = 10) -> np.ndarray:
        """
        Embed multiple texts in batches with retry logic
        Args:
            texts: List of strings to embed
            batch_size: Number of texts per batch
        Returns:
            numpy array of embeddings
        """
        all_embeddings = []
        max_retries = 3
        base_wait = 2
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_num = i // batch_size + 1
            logger.info(f"Processing batch {batch_num} ({len(batch)} texts)...")
            
            # Retry logic with exponential backoff
            for attempt in range(max_retries):
                try:
                    batch_embeddings = self.embed_text(batch)
                    all_embeddings.extend(batch_embeddings)
                    break  # Success, move to next batch
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = base_wait * (2 ** attempt)
                        logger.warning(f"Batch {batch_num} failed (attempt {attempt + 1}/{max_retries}): {e}")
                        logger.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Batch {batch_num} failed after {max_retries} attempts")
                        raise
        
        return np.array(all_embeddings, dtype=np.float32)
    
    def get_embedding_dimension(self) -> int:
        """Get embedding dimension"""
        return self.embedding_dim


# Global embedding service instance
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """Get or create global embedding service instance"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


def embed_text(text: Union[str, List[str]]) -> np.ndarray:
    """Convenience function to embed text"""
    return get_embedding_service().embed_text(text)


def embed_batch(texts: List[str], batch_size: int = 10) -> np.ndarray:
    """Convenience function to embed batch of texts"""
    return get_embedding_service().embed_batch(texts, batch_size)
