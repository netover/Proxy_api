"""
Chaos Engineering Controller

Provides API endpoints for managing chaos engineering experiments,
monitoring active experiments, and controlling fault injection.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

from src.core.chaos.monkey import chaos_monkey, ChaosExperiment, FaultConfig, FaultType, FaultSeverity
from src.core.logging import ContextualLogger
from src.core.security.auth import verify_api_key

logger = ContextualLogger(__name__)

router = APIRouter(prefix="/chaos", tags=["chaos"])


class FaultConfigRequest(BaseModel):
    """Request model for fault configuration"""
    type: str
    severity: str
    probability: float
    duration_ms: int
    target_services: Optional[List[str]] = None
    enabled: bool = True


class ExperimentRequest(BaseModel):
    """Request model for creating experiments"""
    name: str
    description: str
    duration_minutes: int
    faults: List[FaultConfigRequest]
    enabled: bool = True


class ExperimentResponse(BaseModel):
    """Response model for experiments"""
    name: str
    description: str
    duration_minutes: int
    enabled: bool
    status: str
    start_time: Optional[float]
    end_time: Optional[float]
    fault_count: int


@router.get("/status", dependencies=[Depends(verify_api_key)])
async def get_chaos_status():
    """Get current chaos engineering status"""
    try:
        metrics = chaos_monkey.get_safety_metrics()
        active_experiments = chaos_monkey.get_active_experiments()

        return {
            "enabled": chaos_monkey.enabled,
            "active_experiments": len(active_experiments),
            "total_experiments": metrics.get("total_experiments", 0),
            "fault_injections": metrics.get("fault_injections", 0),
            "emergency_stops": metrics.get("emergency_stops", 0),
            "experiments": {
                name: ExperimentResponse(
                    name=exp.name,
                    description=exp.description,
                    duration_minutes=exp.duration_minutes,
                    enabled=exp.enabled,
                    status=exp.status,
                    start_time=exp.start_time,
                    end_time=exp.end_time,
                    fault_count=len(exp.faults)
                ) for name, exp in active_experiments.items()
            }
        }
    except Exception as e:
        logger.error(f"Failed to get chaos status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chaos status")


@router.get("/experiments", dependencies=[Depends(verify_api_key)])
async def list_experiments():
    """List all configured chaos experiments"""
    try:
        experiments = chaos_monkey.list_experiments()

        return {
            "experiments": [
                ExperimentResponse(
                    name=exp.name,
                    description=exp.description,
                    duration_minutes=exp.duration_minutes,
                    enabled=exp.enabled,
                    status=exp.status,
                    start_time=exp.start_time,
                    end_time=exp.end_time,
                    fault_count=len(exp.faults)
                ) for exp in experiments.values()
            ]
        }
    except Exception as e:
        logger.error(f"Failed to list experiments: {e}")
        raise HTTPException(status_code=500, detail="Failed to list experiments")


@router.post("/experiments", dependencies=[Depends(verify_api_key)])
async def create_experiment(request: ExperimentRequest):
    """Create a new chaos experiment"""
    try:
        # Convert request to fault configs
        faults = []
        for fault_req in request.faults:
            fault = FaultConfig(
                type=FaultType(fault_req.type),
                severity=FaultSeverity(fault_req.severity),
                probability=fault_req.probability,
                duration_ms=fault_req.duration_ms,
                target_services=fault_req.target_services or [],
                enabled=fault_req.enabled
            )
            faults.append(fault)

        # Create experiment
        experiment = chaos_monkey.create_experiment(
            name=request.name,
            description=request.description,
            duration_minutes=request.duration_minutes,
            faults=faults
        )

        logger.info(f"Created chaos experiment: {request.name}")

        return ExperimentResponse(
            name=experiment.name,
            description=experiment.description,
            duration_minutes=experiment.duration_minutes,
            enabled=experiment.enabled,
            status=experiment.status,
            start_time=experiment.start_time,
            end_time=experiment.end_time,
            fault_count=len(experiment.faults)
        )

    except Exception as e:
        logger.error(f"Failed to create experiment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create experiment: {str(e)}")


@router.post("/experiments/{experiment_name}/start", dependencies=[Depends(verify_api_key)])
async def start_experiment(experiment_name: str, background_tasks: BackgroundTasks):
    """Start a chaos experiment"""
    try:
        success = await chaos_monkey.start_experiment(experiment_name)

        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to start experiment {experiment_name}. Check if it exists and is not already running."
            )

        logger.info(f"Started chaos experiment: {experiment_name}")
        return {"message": f"Chaos experiment {experiment_name} started successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start experiment {experiment_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start experiment: {str(e)}")


@router.post("/experiments/{experiment_name}/stop", dependencies=[Depends(verify_api_key)])
async def stop_experiment(experiment_name: str):
    """Stop a chaos experiment"""
    try:
        success = await chaos_monkey.stop_experiment(experiment_name)

        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to stop experiment {experiment_name}. Check if it is currently running."
            )

        logger.info(f"Stopped chaos experiment: {experiment_name}")
        return {"message": f"Chaos experiment {experiment_name} stopped successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop experiment {experiment_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop experiment: {str(e)}")


@router.post("/emergency-stop", dependencies=[Depends(verify_api_key)])
async def emergency_stop():
    """Emergency stop all chaos experiments"""
    try:
        await chaos_monkey.emergency_stop()
        logger.warning("Emergency stop triggered for all chaos experiments")
        return {"message": "Emergency stop executed. All chaos experiments have been stopped."}

    except Exception as e:
        logger.error(f"Failed to execute emergency stop: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute emergency stop: {str(e)}")


@router.get("/metrics", dependencies=[Depends(verify_api_key)])
async def get_chaos_metrics():
    """Get chaos engineering metrics and statistics"""
    try:
        metrics = chaos_monkey.get_safety_metrics()
        active_experiments = chaos_monkey.get_active_experiments()

        return {
            "safety_metrics": metrics,
            "active_experiments": [
                {
                    "name": exp.name,
                    "status": exp.status,
                    "start_time": exp.start_time,
                    "duration_minutes": exp.duration_minutes,
                    "fault_count": len(exp.faults)
                } for exp in active_experiments.values()
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get chaos metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chaos metrics")


@router.get("/fault-types", dependencies=[Depends(verify_api_key)])
async def get_fault_types():
    """Get available fault types and severities"""
    return {
        "fault_types": [ft.value for ft in FaultType],
        "severities": [fs.value for fs in FaultSeverity],
        "examples": {
            "latency": {
                "type": "latency",
                "severity": "medium",
                "probability": 0.1,
                "duration_ms": 500,
                "description": "Inject random latency delays"
            },
            "network_failure": {
                "type": "network_failure",
                "severity": "high",
                "probability": 0.05,
                "duration_ms": 1000,
                "description": "Simulate network failures"
            },
            "cpu_exhaustion": {
                "type": "cpu_exhaustion",
                "severity": "critical",
                "probability": 0.02,
                "duration_ms": 2000,
                "description": "Exhaust CPU resources"
            }
        }
    }
