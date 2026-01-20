"""
Financial calculation routes.
"""
from typing import Optional
from datetime import datetime

import numpy as np
from scipy import optimize
from fastapi import APIRouter, Request
from loguru import logger

from src.models.finance import (
    NPVRequest,
    IRRRequest,
    PMTRequest,
    FVRequest,
    PVRequest,
    AmortizationRequest,
)

router = APIRouter()


def calculate_npv(rate: float, cash_flows: list[float]) -> tuple[float, list[float]]:
    """Calculate Net Present Value and present values of each cash flow."""
    present_values = []
    npv = 0.0
    
    for i, cf in enumerate(cash_flows):
        pv = cf / ((1 + rate) ** i)
        present_values.append(round(pv, 10))
        npv += pv
    
    return round(npv, 10), present_values


def calculate_irr(cash_flows: list[float], guess: float = 0.1) -> Optional[float]:
    """
    Calculate Internal Rate of Return using Newton-Raphson method.
    
    Returns None if IRR cannot be calculated.
    """
    def npv_func(rate: float) -> float:
        return sum(cf / ((1 + rate) ** i) for i, cf in enumerate(cash_flows))
    
    try:
        # Try scipy's brentq for robust root finding
        # First find bounds where NPV changes sign
        lower, upper = -0.99, 10.0
        
        if npv_func(lower) * npv_func(upper) < 0:
            irr = optimize.brentq(npv_func, lower, upper)
            return round(irr, 10)
        
        # Fall back to Newton's method
        irr = optimize.newton(npv_func, guess, maxiter=100, tol=1e-10)
        return round(irr, 10)
    except (ValueError, RuntimeError):
        try:
            # Try fsolve as last resort
            result = optimize.fsolve(npv_func, guess, full_output=True)
            irr = result[0][0]
            if abs(npv_func(irr)) < 0.0001:
                return round(irr, 10)
        except Exception:
            pass
    
    return None


def calculate_pmt(rate: float, nper: int, pv: float, fv: float = 0, pmt_type: int = 0) -> float:
    """
    Calculate payment for a loan based on constant payments and constant interest rate.
    
    Args:
        rate: Interest rate per period
        nper: Total number of periods
        pv: Present value (loan amount)
        fv: Future value (balloon payment, default 0)
        pmt_type: 0 = end of period, 1 = beginning of period
    
    Returns:
        Payment amount (negative for cash outflow)
    """
    if rate == 0:
        return -(pv + fv) / nper
    
    factor = (1 + rate) ** nper
    
    if pmt_type == 0:
        pmt = (-pv * factor * rate - fv * rate) / (factor - 1)
    else:
        pmt = (-pv * factor * rate - fv * rate) / ((factor - 1) * (1 + rate))
    
    return round(pmt, 10)


def calculate_fv(rate: float, nper: int, pmt: float, pv: float = 0, pmt_type: int = 0) -> float:
    """Calculate Future Value."""
    if rate == 0:
        return -(pv + pmt * nper)
    
    factor = (1 + rate) ** nper
    
    if pmt_type == 0:
        fv = -pv * factor - pmt * (factor - 1) / rate
    else:
        fv = -pv * factor - pmt * (factor - 1) / rate * (1 + rate)
    
    return round(fv, 10)


def calculate_pv(rate: float, nper: int, pmt: float, fv: float = 0, pmt_type: int = 0) -> float:
    """Calculate Present Value."""
    if rate == 0:
        return -(fv + pmt * nper)
    
    factor = (1 + rate) ** nper
    
    if pmt_type == 0:
        pv = (-fv - pmt * (factor - 1) / rate) / factor
    else:
        pv = (-fv - pmt * (factor - 1) / rate * (1 + rate)) / factor
    
    return round(pv, 10)


@router.post("/finance/npv")
async def npv_endpoint(request: Request, body: NPVRequest):
    """
    Calculate Net Present Value (NPV).
    
    NPV = Σ (Cash Flow_t / (1 + rate)^t)
    
    A positive NPV indicates the investment is profitable at the given discount rate.
    """
    try:
        npv, present_values = calculate_npv(body.rate, body.cash_flows)
        
        return {
            "success": True,
            "data": {
                "npv": npv,
                "rate": body.rate,
                "rate_percentage": round(body.rate * 100, 4),
                "periods": len(body.cash_flows) - 1,
                "present_values": present_values,
                "is_profitable": npv > 0,
                "initial_investment": body.cash_flows[0] if body.cash_flows else 0,
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
    except Exception as e:
        logger.error(f"NPV error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.post("/finance/irr")
async def irr_endpoint(request: Request, body: IRRRequest):
    """
    Calculate Internal Rate of Return (IRR).
    
    IRR is the discount rate that makes NPV = 0.
    """
    try:
        # Validate cash flows have at least one sign change
        signs = [1 if cf >= 0 else -1 for cf in body.cash_flows]
        sign_changes = sum(1 for i in range(1, len(signs)) if signs[i] != signs[i-1])
        
        if sign_changes == 0:
            return {
                "success": False,
                "data": {
                    "error": "Cash flows must have at least one sign change (typically negative initial investment followed by positive returns)",
                },
                "request_id": getattr(request.state, 'request_id', None),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        
        irr = calculate_irr(body.cash_flows, body.guess)
        
        if irr is None:
            return {
                "success": False,
                "data": {
                    "error": "Could not calculate IRR. The cash flows may not have a valid IRR.",
                },
                "request_id": getattr(request.state, 'request_id', None),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        
        # Verify by calculating NPV at IRR
        npv_at_irr, _ = calculate_npv(irr, body.cash_flows)
        
        return {
            "success": True,
            "data": {
                "irr": irr,
                "irr_percentage": round(irr * 100, 4),
                "periods": len(body.cash_flows) - 1,
                "npv_at_irr": npv_at_irr,
                "initial_investment": body.cash_flows[0] if body.cash_flows else 0,
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
    except Exception as e:
        logger.error(f"IRR error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.post("/finance/pmt")
async def pmt_endpoint(request: Request, body: PMTRequest):
    """
    Calculate loan payment (PMT).
    
    Returns the periodic payment for a loan based on constant payments
    and a constant interest rate.
    """
    try:
        pmt_type = 1 if body.payment_type == "beginning" else 0
        payment = calculate_pmt(body.rate, body.nper, body.pv, body.fv, pmt_type)
        
        total_payments = abs(payment) * body.nper
        total_interest = total_payments - body.pv + body.fv
        
        return {
            "success": True,
            "data": {
                "payment": payment,
                "payment_abs": abs(payment),
                "total_payments": round(total_payments, 2),
                "total_interest": round(total_interest, 2),
                "principal": body.pv,
                "periods": body.nper,
                "rate_per_period": body.rate,
                "rate_percentage": round(body.rate * 100, 6),
                "payment_type": body.payment_type,
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
    except Exception as e:
        logger.error(f"PMT error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.post("/finance/fv")
async def fv_endpoint(request: Request, body: FVRequest):
    """
    Calculate Future Value (FV).
    
    Returns the future value of an investment based on periodic, constant payments
    and a constant interest rate.
    """
    try:
        pmt_type = 1 if body.payment_type == "beginning" else 0
        fv = calculate_fv(body.rate, body.nper, body.pmt, body.pv, pmt_type)
        
        return {
            "success": True,
            "data": {
                "future_value": fv,
                "present_value": body.pv,
                "payment": body.pmt,
                "periods": body.nper,
                "rate_per_period": body.rate,
                "rate_percentage": round(body.rate * 100, 6),
                "total_contributions": abs(body.pmt * body.nper) + abs(body.pv),
                "interest_earned": abs(fv) - abs(body.pmt * body.nper) - abs(body.pv),
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
    except Exception as e:
        logger.error(f"FV error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.post("/finance/pv")
async def pv_endpoint(request: Request, body: PVRequest):
    """
    Calculate Present Value (PV).
    
    Returns the present value of a series of future cash flows.
    """
    try:
        pmt_type = 1 if body.payment_type == "beginning" else 0
        pv = calculate_pv(body.rate, body.nper, body.pmt, body.fv, pmt_type)
        
        return {
            "success": True,
            "data": {
                "present_value": pv,
                "future_value": body.fv,
                "payment": body.pmt,
                "periods": body.nper,
                "rate_per_period": body.rate,
                "rate_percentage": round(body.rate * 100, 6),
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
    except Exception as e:
        logger.error(f"PV error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.post("/finance/amortization")
async def amortization_endpoint(request: Request, body: AmortizationRequest):
    """
    Generate loan amortization schedule.
    
    Shows how each payment is split between principal and interest.
    """
    try:
        rate_per_period = body.annual_rate / body.periods_per_year
        payment = abs(calculate_pmt(rate_per_period, body.periods, body.principal, 0, 0))
        
        schedule = []
        balance = body.principal
        cumulative_interest = 0.0
        
        for period in range(1, body.periods + 1):
            interest_payment = balance * rate_per_period
            principal_payment = payment - interest_payment
            
            # Handle last payment rounding
            if period == body.periods:
                principal_payment = balance
                payment = principal_payment + interest_payment
            
            balance -= principal_payment
            cumulative_interest += interest_payment
            
            schedule.append({
                "period": period,
                "payment": round(payment, 2),
                "principal_payment": round(principal_payment, 2),
                "interest_payment": round(interest_payment, 2),
                "principal_balance": round(max(0, balance), 2),
                "cumulative_interest": round(cumulative_interest, 2),
            })
        
        total_payments = sum(row["payment"] for row in schedule)
        total_interest = sum(row["interest_payment"] for row in schedule)
        
        return {
            "success": True,
            "data": {
                "schedule": schedule,
                "summary": {
                    "principal": body.principal,
                    "annual_rate": body.annual_rate,
                    "annual_rate_percentage": round(body.annual_rate * 100, 4),
                    "periods": body.periods,
                    "periods_per_year": body.periods_per_year,
                    "payment": round(payment, 2),
                    "total_payments": round(total_payments, 2),
                    "total_interest": round(total_interest, 2),
                },
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
    except Exception as e:
        logger.error(f"Amortization error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.get("/finance/functions")
async def list_finance_functions():
    """List all supported financial functions."""
    return {
        "success": True,
        "data": {
            "functions": {
                "npv": "Net Present Value - Calculates the present value of future cash flows",
                "irr": "Internal Rate of Return - Discount rate where NPV equals zero",
                "pmt": "Payment - Calculates periodic loan payment",
                "fv": "Future Value - Calculates future value of an investment",
                "pv": "Present Value - Calculates present value of future cash flows",
                "amortization": "Generates detailed loan amortization schedule",
            },
            "formulas": {
                "npv": "NPV = Σ (CF_t / (1 + r)^t)",
                "pmt": "PMT = PV × [r(1+r)^n] / [(1+r)^n - 1]",
                "fv": "FV = PV(1+r)^n + PMT × [(1+r)^n - 1] / r",
                "pv": "PV = FV / (1+r)^n + PMT × [1 - (1+r)^-n] / r",
            },
        },
    }
