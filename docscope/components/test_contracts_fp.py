"""
Tests for Component Contracts - Pure Function Version

This test suite validates:
1. Pure function contract definitions are correct
2. Contract validation works properly with pure functions
3. Contract implementation helpers function correctly
"""

import pytest
import sys
import os

# Using proper relative imports now

from .component_contracts_fp import (
    ViewManagementContract, DataFetchingContract, VisualizationContract, OrchestrationContract,
    validate_view_management_contract, validate_data_fetching_contract, 
    validate_visualization_contract, validate_orchestration_contract,
    create_view_management_contract, create_data_fetching_contract,
    create_visualization_contract, create_orchestration_contract,
    validate_contract_implementation
)

# ============================================================================
# TEST CONTRACT DEFINITIONS
# ============================================================================

class TestContractDefinitions:
    """Test that contract definitions are correct."""
    
    def test_view_management_contract_fields(self):
        """Test ViewManagementContract has correct fields."""
        # Create a mock contract to test field access
        contract = ViewManagementContract(
            extract_view_from_relayout=lambda x: None,
            extract_view_from_figure=lambda x: None,
            preserve_view_in_figure=lambda x, y: x,
            validate_view_state=lambda x: True
        )
        
        assert hasattr(contract, 'extract_view_from_relayout')
        assert hasattr(contract, 'extract_view_from_figure')
        assert hasattr(contract, 'preserve_view_in_figure')
        assert hasattr(contract, 'validate_view_state')
        
        # Test that fields are callable
        assert callable(contract.extract_view_from_relayout)
        assert callable(contract.extract_view_from_figure)
        assert callable(contract.preserve_view_in_figure)
        assert callable(contract.validate_view_state)
    
    def test_data_fetching_contract_fields(self):
        """Test DataFetchingContract has correct fields."""
        contract = DataFetchingContract(
            create_fetch_request=lambda x, y, z: {},
            fetch_data=lambda x: None,
            validate_fetch_request=lambda x: True
        )
        
        assert hasattr(contract, 'create_fetch_request')
        assert hasattr(contract, 'fetch_data')
        assert hasattr(contract, 'validate_fetch_request')
        
        # Test that fields are callable
        assert callable(contract.create_fetch_request)
        assert callable(contract.fetch_data)
        assert callable(contract.validate_fetch_request)
    
    def test_visualization_contract_fields(self):
        """Test VisualizationContract has correct fields."""
        contract = VisualizationContract(
            create_figure=lambda x, y, z: None,
            apply_view_preservation=lambda x, y: x,
            validate_figure=lambda x: True
        )
        
        assert hasattr(contract, 'apply_view_preservation')
        assert hasattr(contract, 'create_figure')
        assert hasattr(contract, 'validate_figure')
        
        # Test that fields are callable
        assert callable(contract.create_figure)
        assert callable(contract.apply_view_preservation)
        assert callable(contract.validate_figure)
    
    def test_orchestration_contract_fields(self):
        """Test OrchestrationContract has correct fields."""
        contract = OrchestrationContract(
            should_fetch_data=lambda x, y, z, w: True,
            create_orchestration_context=lambda a, b, c, d, e, f, g: (None, None, None),
            validate_orchestration_context=lambda x, y, z: True
        )
        
        assert hasattr(contract, 'should_fetch_data')
        assert hasattr(contract, 'create_orchestration_context')
        assert hasattr(contract, 'validate_orchestration_context')
        
        # Test that fields are callable
        assert callable(contract.should_fetch_data)
        assert callable(contract.create_orchestration_context)
        assert callable(contract.validate_orchestration_context)

# ============================================================================
# TEST CONTRACT VALIDATOR
# ============================================================================

class TestContractValidator:
    """Test ContractValidator functionality with pure functions."""
    
    def test_validate_view_management_contract_valid(self):
        """Test validation of valid ViewManagementContract implementation."""
        class ValidViewService:
            def extract_view_from_relayout(self, data):
                return None
            
            def extract_view_from_figure(self, figure):
                return None
            
            def preserve_view_in_figure(self, figure, view_state):
                return figure
            
            def validate_view_state(self, view_state):
                return True
        
        service = ValidViewService()
        result = validate_view_management_contract(service)
        assert result is True
    
    def test_validate_view_management_contract_missing_method(self):
        """Test validation fails when method is missing."""
        class InvalidViewService:
            def extract_view_from_relayout(self, data):
                return None
            
            # Missing extract_view_from_figure method
            
            def preserve_view_in_figure(self, figure, view_state):
                return figure
            
            def validate_view_state(self, view_state):
                return True
        
        service = InvalidViewService()
        result = validate_view_management_contract(service)
        assert result is False
    
    def test_validate_view_management_contract_non_callable(self):
        """Test validation fails when method is not callable."""
        class InvalidViewService:
            def extract_view_from_relayout(self, data):
                return None
            
            def extract_view_from_figure(self, figure):
                return None
            
            def preserve_view_in_figure(self, figure, view_state):
                return figure
            
            # validate_view_state is not callable
            validate_view_state = "not a method"
        
        service = InvalidViewService()
        result = validate_view_management_contract(service)
        assert result is False
    
    def test_validate_data_fetching_contract_valid(self):
        """Test validation of valid DataFetchingContract implementation."""
        class ValidDataService:
            def create_fetch_request(self, view_state, filter_state, enrichment_state):
                return {}
            
            def fetch_data(self, request):
                return None
            
            def validate_fetch_request(self, request):
                return True
        
        service = ValidDataService()
        result = validate_data_fetching_contract(service)
        assert result is True
    
    def test_validate_visualization_contract_valid(self):
        """Test validation of valid VisualizationContract implementation."""
        class ValidVizService:
            def create_figure(self, data, filter_state, enrichment_state):
                return None
            
            def apply_view_preservation(self, figure, view_state):
                return figure
            
            def validate_figure(self, figure):
                return True
        
        service = ValidVizService()
        result = validate_visualization_contract(service)
        assert result is True
    
    def test_validate_orchestration_contract_valid(self):
        """Test validation of valid OrchestrationContract implementation."""
        class ValidOrchestrationService:
            def should_fetch_data(self, view_state, filter_state, enrichment_state, trigger):
                return True
            
            def create_orchestration_context(self, a, b, c, d, e, f, g):
                return (None, None, None)
            
            def validate_orchestration_context(self, view_state, filter_state, enrichment_state):
                return True
        
        service = ValidOrchestrationService()
        result = validate_orchestration_contract(service)
        assert result is True

# ============================================================================
# TEST CONTRACT IMPLEMENTATION HELPER
# ============================================================================

class TestContractImplementationHelper:
    """Test ContractImplementationHelper functionality with pure functions."""
    
    def test_create_view_management_contract_valid(self):
        """Test creating ViewManagementContract from valid service."""
        class ValidViewService:
            def extract_view_from_relayout(self, data):
                return None
            
            def extract_view_from_figure(self, figure):
                return None
            
            def preserve_view_in_figure(self, figure, view_state):
                return figure
            
            def validate_view_state(self, view_state):
                return True
        
        service = ValidViewService()
        contract = create_view_management_contract(service)
        
        assert isinstance(contract, ViewManagementContract)
        assert callable(contract.extract_view_from_relayout)
        assert callable(contract.extract_view_from_figure)
        assert callable(contract.preserve_view_in_figure)
        assert callable(contract.validate_view_state)
    
    def test_create_view_management_contract_invalid(self):
        """Test creating ViewManagementContract from invalid service."""
        class InvalidViewService:
            def extract_view_from_relayout(self, data):
                return None
            
            # Missing required methods
        
        service = InvalidViewService()
        
        with pytest.raises(ValueError, match="Service does not implement ViewManagementContract"):
            create_view_management_contract(service)
    
    def test_create_data_fetching_contract_valid(self):
        """Test creating DataFetchingContract from valid service."""
        class ValidDataService:
            def create_fetch_request(self, view_state, filter_state, enrichment_state):
                return {}
            
            def fetch_data(self, request):
                return None
            
            def validate_fetch_request(self, request):
                return True
        
        service = ValidDataService()
        contract = create_data_fetching_contract(service)
        
        assert isinstance(contract, DataFetchingContract)
        assert callable(contract.create_fetch_request)
        assert callable(contract.fetch_data)
        assert callable(contract.validate_fetch_request)
    
    def test_create_visualization_contract_valid(self):
        """Test creating VisualizationContract from valid service."""
        class ValidVizService:
            def create_figure(self, data, filter_state, enrichment_state):
                return None
            
            def apply_view_preservation(self, figure, view_state):
                return figure
            
            def validate_figure(self, figure):
                return True
        
        service = ValidVizService()
        contract = create_visualization_contract(service)
        
        assert isinstance(contract, VisualizationContract)
        assert callable(contract.create_figure)
        assert callable(contract.apply_view_preservation)
        assert callable(contract.validate_figure)

# ============================================================================
# TEST CONTRACT TESTING UTILITY
# ============================================================================

class TestContractTestingUtility:
    """Test the contract testing utility function with pure functions."""
    
    def test_test_contract_implementation_valid(self):
        """Test contract testing utility with valid service."""
        class ValidViewService:
            def extract_view_from_relayout(self, data):
                return None
            
            def extract_view_from_figure(self, figure):
                return None
            
            def preserve_view_in_figure(self, figure, view_state):
                return figure
            
            def validate_view_state(self, view_state):
                return True
        
        service = ValidViewService()
        result = validate_contract_implementation(service, 'view_management')
        assert result is True
    
    def test_test_contract_implementation_invalid(self):
        """Test contract testing utility with invalid service."""
        class InvalidViewService:
            def extract_view_from_relayout(self, data):
                return None
            
            # Missing required methods
        
        service = InvalidViewService()
        result = validate_contract_implementation(service, 'view_management')
        assert result is False
    
    def test_test_contract_implementation_unknown_type(self):
        """Test contract testing utility with unknown contract type."""
        class ValidService:
            pass
        
        service = ValidService()
        
        # Should return False for unknown contract type
        result = validate_contract_implementation(service, 'unknown')
        assert result is False

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v"])
