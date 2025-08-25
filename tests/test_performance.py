#!/usr/bin/env python3
"""
HNC Legal Questionnaire System - Performance Testing Script
Tests API endpoints under various load conditions and measures performance metrics
"""

import asyncio
import aiohttp
import time
import json
import statistics
import sys
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass
import logging
import concurrent.futures
import psutil
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance measurement data"""
    endpoint: str
    response_time: float
    status_code: int
    success: bool
    timestamp: float
    error_message: str = ""


@dataclass
class LoadTestResult:
    """Load test results summary"""
    endpoint: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    min_response_time: float
    max_response_time: float
    percentile_95: float
    percentile_99: float
    requests_per_second: float
    error_rate: float
    errors: List[str]


class PerformanceTester:
    """Performance testing suite for HNC Legal Questionnaire API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.auth_token = "mock_token"
        self.results: List[PerformanceMetric] = []
        self.test_data = self._generate_test_data()
        
    def _generate_test_data(self) -> Dict[str, Any]:
        """Generate test data for performance testing"""
        return {
            "bioData": {
                "fullName": "Performance Test User",
                "maritalStatus": "Single",
                "children": "No children"
            },
            "financialData": {
                "assets": [
                    {
                        "type": "Savings",
                        "description": "Bank savings account",
                        "value": 100000
                    }
                ],
                "liabilities": "None",
                "incomeSources": "Employment"
            },
            "economicContext": {
                "economicStanding": "Middle class",
                "distributionPrefs": "Simple distribution"
            },
            "objectives": {
                "objective": "Basic will creation",
                "details": "Simple estate planning"
            },
            "lawyerNotes": "Performance testing data"
        }
    
    def test_endpoint_performance(self, endpoint: str, method: str = "GET", 
                                  data: Dict = None, headers: Dict = None) -> PerformanceMetric:
        """Test single endpoint performance"""
        url = f"{self.base_url}{endpoint}"
        
        if headers is None:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == "POST":
                headers["Content-Type"] = "application/json"
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            end_time = time.time()
            response_time = end_time - start_time
            
            return PerformanceMetric(
                endpoint=endpoint,
                response_time=response_time,
                status_code=response.status_code,
                success=response.status_code < 400,
                timestamp=start_time,
                error_message=""
            )
            
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            
            return PerformanceMetric(
                endpoint=endpoint,
                response_time=response_time,
                status_code=0,
                success=False,
                timestamp=start_time,
                error_message=str(e)
            )
    
    def load_test_endpoint(self, endpoint: str, method: str = "GET", 
                          data: Dict = None, concurrent_users: int = 10, 
                          requests_per_user: int = 10) -> LoadTestResult:
        """Perform load testing on a specific endpoint"""
        print(f"\n🔄 Load testing {endpoint} with {concurrent_users} concurrent users, {requests_per_user} requests each...")
        
        def make_requests(user_id: int) -> List[PerformanceMetric]:
            """Make multiple requests for a single user"""
            user_results = []
            for i in range(requests_per_user):
                metric = self.test_endpoint_performance(endpoint, method, data)
                metric.endpoint = f"{endpoint}_user_{user_id}_req_{i}"
                user_results.append(metric)
                time.sleep(0.1)  # Small delay between requests
            return user_results
        
        start_time = time.time()
        all_metrics = []
        
        # Use ThreadPoolExecutor for concurrent testing
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            future_to_user = {
                executor.submit(make_requests, user_id): user_id 
                for user_id in range(concurrent_users)
            }
            
            for future in concurrent.futures.as_completed(future_to_user):
                user_id = future_to_user[future]
                try:
                    user_metrics = future.result()
                    all_metrics.extend(user_metrics)
                except Exception as e:
                    logger.error(f"User {user_id} failed: {e}")
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Calculate statistics
        successful_metrics = [m for m in all_metrics if m.success]
        failed_metrics = [m for m in all_metrics if not m.success]
        
        if successful_metrics:
            response_times = [m.response_time for m in successful_metrics]
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            
            # Calculate percentiles
            sorted_times = sorted(response_times)
            percentile_95 = sorted_times[int(0.95 * len(sorted_times))] if sorted_times else 0
            percentile_99 = sorted_times[int(0.99 * len(sorted_times))] if sorted_times else 0
        else:
            avg_response_time = min_response_time = max_response_time = 0
            percentile_95 = percentile_99 = 0
        
        total_requests = len(all_metrics)
        successful_requests = len(successful_metrics)
        failed_requests = len(failed_metrics)
        requests_per_second = total_requests / total_duration if total_duration > 0 else 0
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
        
        errors = [m.error_message for m in failed_metrics if m.error_message]
        
        return LoadTestResult(
            endpoint=endpoint,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            percentile_95=percentile_95,
            percentile_99=percentile_99,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            errors=errors[:5]  # Keep first 5 errors
        )
    
    def test_system_resources(self) -> Dict[str, Any]:
        """Monitor system resource usage during testing"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available_gb": psutil.virtual_memory().available / (1024**3),
            "disk_usage_percent": psutil.disk_usage('/').percent,
            "network_sent_mb": psutil.net_io_counters().bytes_sent / (1024**2),
            "network_recv_mb": psutil.net_io_counters().bytes_recv / (1024**2)
        }
    
    def run_comprehensive_performance_test(self) -> Dict[str, Any]:
        """Run comprehensive performance testing suite"""
        print("🚀 Starting Comprehensive Performance Testing")
        print("=" * 60)
        
        start_time = datetime.now()
        initial_resources = self.test_system_resources()
        
        # Define test scenarios
        test_scenarios = [
            # Light load tests
            {"endpoint": "/health", "method": "GET", "data": None, "users": 5, "requests": 5},
            {"endpoint": "/", "method": "GET", "data": None, "users": 5, "requests": 5},
            
            # Authentication tests
            {"endpoint": "/auth/login", "method": "POST", 
             "data": {"username": "admin", "password": "admin123"}, "users": 3, "requests": 3},
            
            # Data submission tests
            {"endpoint": "/questionnaire/submit", "method": "POST", 
             "data": self.test_data, "users": 5, "requests": 3},
            
            # Data retrieval tests
            {"endpoint": "/questionnaire/data", "method": "GET", "data": None, "users": 5, "requests": 5},
            {"endpoint": "/assets/summary", "method": "GET", "data": None, "users": 5, "requests": 5},
            
            # AI processing tests (CPU intensive)
            {"endpoint": "/ai/generate-proposal", "method": "POST", 
             "data": {"questionnaireData": self.test_data, "distributionPrefs": "Simple"}, 
             "users": 3, "requests": 2},
        ]
        
        # Run tests
        test_results = []
        for i, scenario in enumerate(test_scenarios):
            print(f"\n📊 Test {i+1}/{len(test_scenarios)}: {scenario['endpoint']}")
            
            result = self.load_test_endpoint(
                endpoint=scenario["endpoint"],
                method=scenario["method"],
                data=scenario["data"],
                concurrent_users=scenario["users"],
                requests_per_user=scenario["requests"]
            )
            
            test_results.append(result)
            
            # Print immediate results
            print(f"   ✅ Success Rate: {100 - result.error_rate:.1f}%")
            print(f"   ⚡ Avg Response: {result.average_response_time*1000:.1f}ms")
            print(f"   🔥 Throughput: {result.requests_per_second:.1f} req/s")
            
            # Brief pause between tests
            time.sleep(1)
        
        final_resources = self.test_system_resources()
        end_time = datetime.now()
        
        # Generate comprehensive report
        report = {
            "test_summary": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": (end_time - start_time).total_seconds(),
                "total_tests": len(test_results),
                "total_requests": sum(r.total_requests for r in test_results),
                "total_successful": sum(r.successful_requests for r in test_results),
                "total_failed": sum(r.failed_requests for r in test_results),
                "overall_error_rate": sum(r.failed_requests for r in test_results) / 
                                    max(sum(r.total_requests for r in test_results), 1) * 100
            },
            "endpoint_results": [
                {
                    "endpoint": r.endpoint,
                    "total_requests": r.total_requests,
                    "success_rate": 100 - r.error_rate,
                    "avg_response_ms": r.average_response_time * 1000,
                    "min_response_ms": r.min_response_time * 1000,
                    "max_response_ms": r.max_response_time * 1000,
                    "p95_response_ms": r.percentile_95 * 1000,
                    "p99_response_ms": r.percentile_99 * 1000,
                    "throughput_rps": r.requests_per_second,
                    "error_rate": r.error_rate,
                    "sample_errors": r.errors
                }
                for r in test_results
            ],
            "system_resources": {
                "initial": initial_resources,
                "final": final_resources,
                "cpu_increase": final_resources["cpu_percent"] - initial_resources["cpu_percent"],
                "memory_increase": final_resources["memory_percent"] - initial_resources["memory_percent"]
            }
        }
        
        return report
    
    def print_performance_report(self, report: Dict[str, Any]):
        """Print formatted performance report"""
        print("\n" + "=" * 80)
        print("📈 PERFORMANCE TEST REPORT")
        print("=" * 80)
        
        summary = report["test_summary"]
        print(f"🕐 Test Duration: {summary['duration_seconds']:.1f} seconds")
        print(f"📊 Total Requests: {summary['total_requests']}")
        print(f"✅ Successful: {summary['total_successful']}")
        print(f"❌ Failed: {summary['total_failed']}")
        print(f"📈 Overall Success Rate: {100 - summary['overall_error_rate']:.1f}%")
        
        print("\n📋 ENDPOINT PERFORMANCE DETAILS")
        print("-" * 80)
        print(f"{'Endpoint':<25} {'Requests':<10} {'Success%':<10} {'Avg(ms)':<10} {'P95(ms)':<10} {'RPS':<8}")
        print("-" * 80)
        
        for result in report["endpoint_results"]:
            print(f"{result['endpoint']:<25} {result['total_requests']:<10} "
                  f"{result['success_rate']:<9.1f}% {result['avg_response_ms']:<9.0f} "
                  f"{result['p95_response_ms']:<9.0f} {result['throughput_rps']:<7.1f}")
        
        print("\n💾 SYSTEM RESOURCE USAGE")
        print("-" * 40)
        resources = report["system_resources"]
        print(f"CPU Usage: {resources['final']['cpu_percent']:.1f}% "
              f"({resources['cpu_increase']:+.1f}%)")
        print(f"Memory Usage: {resources['final']['memory_percent']:.1f}% "
              f"({resources['memory_increase']:+.1f}%)")
        print(f"Available Memory: {resources['final']['memory_available_gb']:.1f} GB")
        
        # Performance assessment
        print("\n🎯 PERFORMANCE ASSESSMENT")
        print("-" * 40)
        
        avg_response_times = [r["avg_response_ms"] for r in report["endpoint_results"]]
        overall_avg = statistics.mean(avg_response_times) if avg_response_times else 0
        success_rates = [r["success_rate"] for r in report["endpoint_results"]]
        min_success_rate = min(success_rates) if success_rates else 0
        
        if overall_avg < 500 and min_success_rate > 95:
            print("🟢 EXCELLENT: System performs well under load")
        elif overall_avg < 1000 and min_success_rate > 90:
            print("🟡 GOOD: System performance is acceptable")
        elif overall_avg < 2000 and min_success_rate > 80:
            print("🟠 FAIR: System shows some performance issues")
        else:
            print("🔴 POOR: System needs performance optimization")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS")
        print("-" * 40)
        
        slow_endpoints = [r for r in report["endpoint_results"] if r["avg_response_ms"] > 1000]
        if slow_endpoints:
            print("• Optimize slow endpoints:")
            for endpoint in slow_endpoints[:3]:
                print(f"  - {endpoint['endpoint']}: {endpoint['avg_response_ms']:.0f}ms average")
        
        failing_endpoints = [r for r in report["endpoint_results"] if r["error_rate"] > 5]
        if failing_endpoints:
            print("• Fix endpoints with high error rates:")
            for endpoint in failing_endpoints:
                print(f"  - {endpoint['endpoint']}: {endpoint['error_rate']:.1f}% error rate")
        
        if resources["final"]["cpu_percent"] > 80:
            print("• Consider CPU optimization or scaling")
        
        if resources["final"]["memory_percent"] > 85:
            print("• Monitor memory usage and consider optimization")
        
        print(f"\n📄 Report saved at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """Main performance testing execution"""
    print("🔍 HNC Legal Questionnaire - Performance Testing Suite")
    print("=" * 60)
    
    # Initialize tester
    tester = PerformanceTester()
    
    # Check if backend is available
    try:
        health_check = tester.test_endpoint_performance("/health")
        if not health_check.success:
            print("❌ Backend server is not responding. Please start the backend first.")
            print("   Run: cd backend && python -m uvicorn main:app --reload")
            return False
    except Exception as e:
        print(f"❌ Failed to connect to backend: {e}")
        return False
    
    print("✅ Backend server is running and responsive")
    
    # Run comprehensive performance tests
    try:
        report = tester.run_comprehensive_performance_test()
        tester.print_performance_report(report)
        
        # Save detailed report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"test_reports/performance_report_{timestamp}.json"
        
        import os
        os.makedirs("test_reports", exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance testing failed: {e}")
        logger.exception("Performance testing error")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)