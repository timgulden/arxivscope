#!/usr/bin/env python3
"""
UMAP Environment Reset Script

This script performs a complete reset of the UMAP 2D embedding environment.
Use this when you've ingested papers from significantly different semantic domains
(e.g., Roman history vs. quantum physics) that don't map well into the existing space.

Process:
1. Stop 2D embedding enrichment service
2. Clear both title and abstract 2D embedding columns
3. Take a random sample of papers with both embeddings
4. Compute new UMAP model on the sample
5. Restart incremental processing
"""

import sys
import os
import logging
import time
import subprocess
import signal
import psutil
import argparse
import random
from typing import List, Dict, Any, Optional, Tuple
import psycopg2
import numpy as np
import pickle
from sklearn.preprocessing import StandardScaler
import umap.umap_ as umap

# Add paths for imports
sys.path.append('../doctrove-api')
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

# Import our processing functions
from combined_2d_processor import get_database_connection, save_2d_embeddings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# UMAP configuration
UMAP_CONFIG = {
    'n_components': 2,
    'n_neighbors': 15,
    'min_dist': 0.1,
    'metric': 'cosine',
    'random_state': 42
}

class UMAPEnvironmentReset:
    """
    Handles the complete UMAP environment reset process.
    """
    
    def __init__(self, sample_size: int = 100000, model_path: str = 'umap_model.pkl', use_stratified: bool = False):
        self.sample_size = sample_size
        self.model_path = model_path
        self.use_stratified = use_stratified
        self.connection_params = {
            'host': DB_HOST,
            'port': DB_PORT,
            'database': DB_NAME,
            'user': DB_USER,
            'password': DB_PASSWORD
        }
    
    def stop_enrichment_services(self) -> bool:
        """
        Stop any running enrichment services (event listener, etc.).
        
        Returns:
            True if services were stopped successfully
        """
        logger.debug("Stopping enrichment services...")
        
        try:
            # Find and stop event listener processes
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any('event_listener.py' in arg for arg in cmdline):
                        logger.debug(f"Stopping event listener process {proc.info['pid']}")
                        proc.terminate()
                        proc.wait(timeout=10)
                except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                    pass
            
            # Give services time to shut down
            time.sleep(2)
            
            # Check if any services are still running
            running_services = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any('event_listener.py' in arg for arg in cmdline):
                        running_services.append(proc.info['pid'])
                except psutil.NoSuchProcess:
                    pass
            
            if running_services:
                logger.warning(f"Some services still running: {running_services}")
                return False
            
            logger.debug("Enrichment services stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping enrichment services: {e}")
            return False
    
    def clear_2d_embeddings(self) -> bool:
        """
        Clear both title and abstract 2D embedding columns.
        
        Returns:
            True if clearing was successful
        """
        logger.debug("Clearing 2D embeddings from database...")
        
        try:
            with get_database_connection() as conn:
                with conn.cursor() as cur:
                    # Get count before clearing
                    cur.execute("""
                        SELECT 
                            COUNT(*) FILTER (WHERE doctrove_embedding_2d IS NOT NULL) as embedding_2d_count
                        FROM doctrove_papers
                    """)
                    row = cur.fetchone()
                    embedding_count = row[0] if row[0] else 0
                    
                    logger.debug(f"Found {embedding_count} 2D embeddings to clear")
                    
                    # Clear 2D embeddings
                    cur.execute("""
                        UPDATE doctrove_papers 
                        SET 
                            doctrove_embedding_2d = NULL,
                            embedding_2d_updated_at = NULL
                    """)
                    
                    updated_count = cur.rowcount
                    conn.commit()
                    
                    logger.debug(f"Cleared 2D embeddings for {updated_count} papers")
                    return True
                    
        except Exception as e:
            logger.error(f"Error clearing 2D embeddings: {e}")
            return False
    
    def get_papers_with_embeddings(self) -> List[Dict[str, Any]]:
        """
        Get all papers that have both title and abstract embeddings.
        
        Returns:
            List of paper dictionaries with embeddings
        """
        logger.debug("Loading papers with unified embeddings...")
        
        try:
            with get_database_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            doctrove_paper_id,
                            doctrove_title,
                            doctrove_abstract,
                            doctrove_embedding,
                            doctrove_source
                        FROM doctrove_papers 
                        WHERE doctrove_embedding IS NOT NULL 
                        ORDER BY doctrove_paper_id
                    """)
                    
                    papers = []
                    for row in cur.fetchall():
                        papers.append({
                            'doctrove_paper_id': row[0],
                            'doctrove_title': row[1],
                            'doctrove_abstract': row[2],
                            'doctrove_embedding': row[3],
                            'doctrove_source': row[4]
                        })
                    
                    logger.debug(f"Found {len(papers)} papers with unified embeddings")
                    return papers
                    
        except Exception as e:
            logger.error(f"Error loading papers with embeddings: {e}")
            return []
    
    def sample_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Take a sample of papers for UMAP training.
        For production: Use all papers (up to 100,000)
        For testing: Use specified sample size
        
        Args:
            papers: List of all papers with embeddings
            
        Returns:
            Sample of papers
        """
        # For production: always use 100,000 or all available papers
        production_sample_size = 100000
        
        if len(papers) <= production_sample_size:
            logger.debug(f"Using all {len(papers)} papers (production mode: up to {production_sample_size})")
            return papers
        
        # If we have more than 100,000 papers, sample 100,000
        logger.debug(f"Taking sample of {production_sample_size} papers from {len(papers)} total (production mode)")
        
        # Enhanced sampling: shuffle first, then sample
        # This ensures we don't have any ordering bias from the database query
        shuffled_papers = papers.copy()
        random.shuffle(shuffled_papers)
        sampled_papers = shuffled_papers[:production_sample_size]
        
        # Log sample statistics for verification
        self._log_sample_statistics(sampled_papers, papers)
        
        # Log some sample titles for verification
        sample_titles = [p['doctrove_title'][:50] + "..." for p in sampled_papers[:5]]
        logger.debug(f"Sample titles: {sample_titles}")
        
        return sampled_papers
    
    def _log_sample_statistics(self, sampled_papers: List[Dict[str, Any]], all_papers: List[Dict[str, Any]]) -> None:
        """
        Log statistics about the sample to verify representativeness.
        
        Args:
            sampled_papers: The sampled papers
            all_papers: All available papers
        """
        try:
            # Analyze source distribution if available
            if 'doctrove_source' in sampled_papers[0]:
                all_sources = {}
                sample_sources = {}
                
                for paper in all_papers:
                    source = paper.get('doctrove_source', 'unknown')
                    all_sources[source] = all_sources.get(source, 0) + 1
                
                for paper in sampled_papers:
                    source = paper.get('doctrove_source', 'unknown')
                    sample_sources[source] = sample_sources.get(source, 0) + 1
                
                logger.debug("Source distribution analysis:")
                for source in all_sources:
                    all_count = all_sources[source]
                    sample_count = sample_sources.get(source, 0)
                    all_pct = (all_count / len(all_papers)) * 100
                    sample_pct = (sample_count / len(sampled_papers)) * 100
                    logger.debug(f"  {source}: {all_count} ({all_pct:.1f}%) -> {sample_count} ({sample_pct:.1f}%)")
            
            # Analyze title length distribution (proxy for content type)
            all_title_lengths = [len(p['doctrove_title']) for p in all_papers]
            sample_title_lengths = [len(p['doctrove_title']) for p in sampled_papers]
            
            logger.debug(f"Title length stats - All: avg={np.mean(all_title_lengths):.1f}, std={np.std(all_title_lengths):.1f}")
            logger.debug(f"Title length stats - Sample: avg={np.mean(sample_title_lengths):.1f}, std={np.std(sample_title_lengths):.1f}")
            
        except Exception as e:
            logger.warning(f"Could not analyze sample statistics: {e}")
    
    def sample_papers_stratified(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Take a stratified random sample to ensure representation across sources.
        
        Args:
            papers: List of all papers with embeddings
            
        Returns:
            Stratified random sample of papers
        """
        if len(papers) <= self.sample_size:
            logger.debug(f"Using all {len(papers)} papers (sample size {self.sample_size} not needed)")
            return papers
        
        logger.debug(f"Taking stratified random sample of {self.sample_size} papers from {len(papers)} total")
        
        # Group papers by source
        papers_by_source = {}
        for paper in papers:
            source = paper.get('doctrove_source', 'unknown')
            if source not in papers_by_source:
                papers_by_source[source] = []
            papers_by_source[source].append(paper)
        
        # Calculate proportional allocation
        total_papers = len(papers)
        sampled_papers = []
        
        for source, source_papers in papers_by_source.items():
            source_count = len(source_papers)
            source_proportion = source_count / total_papers
            source_sample_size = max(1, int(self.sample_size * source_proportion))
            
            # Ensure we don't exceed available papers
            source_sample_size = min(source_sample_size, source_count)
            
            # Random sample from this source
            source_sample = random.sample(source_papers, source_sample_size)
            sampled_papers.extend(source_sample)
            
            logger.debug(f"Source '{source}': {source_count} papers -> {source_sample_size} sampled")
        
        # If we have fewer papers than requested, add more randomly
        if len(sampled_papers) < self.sample_size:
            remaining_papers = [p for p in papers if p not in sampled_papers]
            additional_needed = self.sample_size - len(sampled_papers)
            if remaining_papers:
                additional_sample = random.sample(remaining_papers, min(additional_needed, len(remaining_papers)))
                sampled_papers.extend(additional_sample)
                logger.debug(f"Added {len(additional_sample)} additional papers to reach target size")
        
        # Shuffle the final sample to avoid source clustering
        random.shuffle(sampled_papers)
        
        # Log sample statistics
        self._log_sample_statistics(sampled_papers, papers)
        
        # Log some sample titles for verification
        sample_titles = [p['doctrove_title'][:50] + "..." for p in sampled_papers[:5]]
        logger.debug(f"Stratified sample titles: {sample_titles}")
        
        return sampled_papers
    
    def extract_embeddings_from_papers(self, papers: List[Dict[str, Any]]) -> Tuple[List[np.ndarray], List[str], List[str]]:
        """
        Extract embeddings from papers for UMAP training.
        
        Args:
            papers: List of paper dictionaries
            
        Returns:
            Tuple of (embeddings, paper_ids, embedding_types)
        """
        embeddings = []
        paper_ids = []
        embedding_types = []
        
        for paper in papers:
            paper_id = paper['doctrove_paper_id']
            
            # Process unified embedding
            try:
                embedding_data = paper['doctrove_embedding']
                if isinstance(embedding_data, str):
                    embedding_data = embedding_data.strip('[]').split(',')
                    embedding = np.array([float(x.strip()) for x in embedding_data], dtype=np.float32)
                else:
                    embedding = np.array(embedding_data, dtype=np.float32)
                
                embeddings.append(embedding)
                paper_ids.append(paper_id)
                embedding_types.append('unified')
            except Exception as e:
                logger.warning(f"Failed to process unified embedding for paper {paper_id}: {e}")
        
        logger.debug(f"Extracted {len(embeddings)} unified embeddings")
        return embeddings, paper_ids, embedding_types
    
    def train_new_umap_model(self, embeddings: List[np.ndarray]) -> Tuple[umap.UMAP, StandardScaler]:
        """
        Train a new UMAP model on the sample embeddings.
        
        Args:
            embeddings: List of embedding arrays
            
        Returns:
            Tuple of (trained_umap_model, fitted_scaler)
        """
        logger.debug(f"Training new UMAP model on {len(embeddings)} embeddings...")
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings)
        
        # Standardize embeddings
        scaler = StandardScaler()
        embeddings_scaled = scaler.fit_transform(embeddings_array)
        
        # Train UMAP model
        model = umap.UMAP(**UMAP_CONFIG)
        model.fit(embeddings_scaled)
        
        logger.debug("UMAP model training completed")
        return model, scaler
    
    def save_umap_model(self, model: umap.UMAP, scaler: StandardScaler) -> bool:
        """
        Save the trained UMAP model and scaler.
        
        Args:
            model: Trained UMAP model
            scaler: Fitted StandardScaler
            
        Returns:
            True if saving was successful
        """
        try:
            # Backup existing model if it exists
            if os.path.exists(self.model_path):
                backup_path = f"{self.model_path}.backup"
                logger.debug(f"Backing up existing model to {backup_path}")
                os.rename(self.model_path, backup_path)
            
            # Save new model
            logger.debug(f"Saving new UMAP model to {self.model_path}")
            with open(self.model_path, 'wb') as f:
                pickle.dump((model, scaler), f)
            
            logger.debug("UMAP model saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving UMAP model: {e}")
            return False
    
    def generate_2d_embeddings_for_sample(self, papers: List[Dict[str, Any]], model: umap.UMAP, scaler: StandardScaler) -> bool:
        """
        Generate 2D embeddings for the sample papers using the new model.
        
        Args:
            papers: List of sample papers
            model: Trained UMAP model
            scaler: Fitted StandardScaler
            
        Returns:
            True if successful
        """
        logger.debug("Generating 2D embeddings for sample papers...")
        
        try:
            # Extract embeddings
            embeddings, paper_ids, embedding_types = self.extract_embeddings_from_papers(papers)
            
            if not embeddings:
                logger.error("No embeddings extracted from sample papers")
                return False
            
            # Generate 2D embeddings
            embeddings_array = np.array(embeddings)
            embeddings_scaled = scaler.transform(embeddings_array)
            embeddings_2d = model.transform(embeddings_scaled)
            
            # Save to database
            embeddings_2d_list = [emb.tolist() for emb in embeddings_2d]
            saved_count = save_2d_embeddings(paper_ids, embedding_types, embeddings_2d_list)
            
            logger.debug(f"Generated and saved 2D embeddings for {saved_count} embeddings")
            return True
            
        except Exception as e:
            logger.error(f"Error generating 2D embeddings for sample: {e}")
            return False
    
    def start_incremental_processing(self) -> bool:
        """
        Start the incremental processing service.
        
        Returns:
            True if service started successfully
        """
        logger.debug("Starting incremental processing...")
        
        try:
            # Start event listener in background
            cmd = [sys.executable, 'event_listener.py']
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Give it a moment to start
            time.sleep(3)
            
            # Check if it's running
            if process.poll() is None:
                logger.debug(f"Event listener started with PID {process.pid}")
                return True
            else:
                stdout, stderr = process.communicate()
                logger.error(f"Event listener failed to start: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting incremental processing: {e}")
            return False
    
    def run_complete_reset(self) -> bool:
        """
        Run the complete UMAP environment reset process.
        
        Returns:
            True if reset was successful
        """
        logger.debug("=" * 60)
        logger.debug("STARTING UMAP ENVIRONMENT RESET")
        logger.debug("=" * 60)
        
        try:
            # Step 1: Stop enrichment services
            if not self.stop_enrichment_services():
                logger.error("Failed to stop enrichment services")
                return False
            
            # Step 2: Clear 2D embeddings
            if not self.clear_2d_embeddings():
                logger.error("Failed to clear 2D embeddings")
                return False
            
            # Step 3: Get papers with embeddings
            papers = self.get_papers_with_embeddings()
            if not papers:
                logger.error("No papers found with embeddings")
                return False
            
            # Step 4: Sample papers
            if self.use_stratified:
                sampled_papers = self.sample_papers_stratified(papers)
            else:
                sampled_papers = self.sample_papers(papers)
            
            # Step 5: Train new UMAP model
            embeddings, _, _ = self.extract_embeddings_from_papers(sampled_papers)
            if not embeddings:
                logger.error("No embeddings extracted for UMAP training")
                return False
            
            model, scaler = self.train_new_umap_model(embeddings)
            
            # Step 6: Save new model
            if not self.save_umap_model(model, scaler):
                logger.error("Failed to save UMAP model")
                return False
            
            # Step 7: Generate 2D embeddings for sample
            if not self.generate_2d_embeddings_for_sample(sampled_papers, model, scaler):
                logger.error("Failed to generate 2D embeddings for sample")
                return False
            
            # Step 8: Start incremental processing
            if not self.start_incremental_processing():
                logger.error("Failed to start incremental processing")
                return False
            
            logger.debug("=" * 60)
            logger.debug("UMAP ENVIRONMENT RESET COMPLETED SUCCESSFULLY")
            logger.debug("=" * 60)
            logger.debug(f"New UMAP model trained on {len(sampled_papers)} papers")
            logger.debug(f"Sample papers now have 2D embeddings")
            logger.debug("Incremental processing is running for remaining papers")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during UMAP reset: {e}")
            return False

def main():
    """Main entry point for the UMAP reset script."""
    parser = argparse.ArgumentParser(description='Reset UMAP environment for new semantic domains')
    parser.add_argument('--sample-size', type=int, default=100000,
                       help='Number of papers to sample for UMAP training (TESTING ONLY - production always uses 100000 or all available papers)')
    parser.add_argument('--model-path', default='umap_model.pkl',
                       help='Path to save UMAP model (default: umap_model.pkl)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without actually doing it')
    parser.add_argument('--stratified', action='store_true',
                       help='Use stratified sampling to ensure representation across sources')
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.debug("DRY RUN MODE - No changes will be made")
        logger.debug(f"Sample size: {args.sample_size}")
        logger.debug(f"Model path: {args.model_path}")
        logger.debug(f"Stratified sampling: {args.stratified}")
        
        # Just check what papers we have
        resetter = UMAPEnvironmentReset(args.sample_size, args.model_path, args.stratified)
        papers = resetter.get_papers_with_embeddings()
        logger.debug(f"Would sample from {len(papers)} papers with embeddings")
        return
    
    # Run the reset
    resetter = UMAPEnvironmentReset(args.sample_size, args.model_path, args.stratified)
    success = resetter.run_complete_reset()
    
    if success:
        print("\n✅ UMAP environment reset completed successfully!")
        print("The system is now ready for incremental processing of new papers.")
    else:
        print("\n❌ UMAP environment reset failed!")
        print("Check the logs above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main() 