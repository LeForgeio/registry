"""
Excel-like operation routes.
"""
import re
import fnmatch
from typing import Any, Optional, Union
from datetime import datetime

import pandas as pd
import numpy as np
from fastapi import APIRouter, Request
from loguru import logger

from src.models.excel import (
    VLookupRequest,
    SumIfRequest,
    PivotRequest,
    HLookupRequest,
    CountIfRequest,
    AverageIfRequest,
)

router = APIRouter()


def parse_criteria(criteria: str, value: Any) -> bool:
    """
    Parse Excel-style criteria and evaluate against a value.
    
    Supports:
    - Exact match: "Apple"
    - Greater than: ">100"
    - Less than: "<50"
    - Greater or equal: ">=100"
    - Less or equal: "<=50"
    - Not equal: "<>Apple"
    - Wildcards: "*ing", "A?ple", "*"
    """
    if criteria is None:
        return False
    
    criteria_str = str(criteria).strip()
    
    # Handle comparison operators
    if criteria_str.startswith(">="):
        try:
            return float(value) >= float(criteria_str[2:])
        except (ValueError, TypeError):
            return False
    elif criteria_str.startswith("<="):
        try:
            return float(value) <= float(criteria_str[2:])
        except (ValueError, TypeError):
            return False
    elif criteria_str.startswith("<>"):
        return str(value) != criteria_str[2:]
    elif criteria_str.startswith(">"):
        try:
            return float(value) > float(criteria_str[1:])
        except (ValueError, TypeError):
            return False
    elif criteria_str.startswith("<"):
        try:
            return float(value) < float(criteria_str[1:])
        except (ValueError, TypeError):
            return False
    elif criteria_str.startswith("="):
        compare_val = criteria_str[1:]
        try:
            return float(value) == float(compare_val)
        except (ValueError, TypeError):
            return str(value) == compare_val
    
    # Handle wildcards (* and ?)
    if "*" in criteria_str or "?" in criteria_str:
        return fnmatch.fnmatch(str(value), criteria_str)
    
    # Exact match (case-insensitive for strings)
    try:
        return float(value) == float(criteria_str)
    except (ValueError, TypeError):
        return str(value).lower() == criteria_str.lower()


@router.post("/excel/vlookup")
async def vlookup(request: Request, body: VLookupRequest):
    """
    Perform VLOOKUP operation (Vertical Lookup).
    
    Searches for a value in the first column of a table array and returns
    a value in the same row from a specified column.
    """
    try:
        table = body.table_array
        lookup_val = body.lookup_value
        col_idx = body.col_index - 1  # Convert to 0-based index
        
        if col_idx >= len(table[0]) if table else 0:
            raise ValueError(f"Column index {body.col_index} exceeds table width")
        
        result = None
        found = False
        row_index = None
        
        if body.exact_match:
            # Exact match
            for i, row in enumerate(table):
                if len(row) > 0 and row[0] == lookup_val:
                    result = row[col_idx] if col_idx < len(row) else None
                    found = True
                    row_index = i
                    break
        else:
            # Approximate match (assumes sorted data, returns largest value <= lookup)
            best_match_idx = None
            best_match_val = None
            
            for i, row in enumerate(table):
                if len(row) > 0:
                    cell_val = row[0]
                    try:
                        if cell_val <= lookup_val:
                            if best_match_val is None or cell_val > best_match_val:
                                best_match_val = cell_val
                                best_match_idx = i
                    except TypeError:
                        continue
            
            if best_match_idx is not None:
                result = table[best_match_idx][col_idx] if col_idx < len(table[best_match_idx]) else None
                found = True
                row_index = best_match_idx
        
        return {
            "success": True,
            "data": {
                "result": result,
                "found": found,
                "lookup_value": lookup_val,
                "row_index": row_index,
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
    except Exception as e:
        logger.error(f"VLOOKUP error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.post("/excel/hlookup")
async def hlookup(request: Request, body: HLookupRequest):
    """
    Perform HLOOKUP operation (Horizontal Lookup).
    
    Searches for a value in the first row of a table array and returns
    a value in the same column from a specified row.
    """
    try:
        table = body.table_array
        lookup_val = body.lookup_value
        row_idx = body.row_index - 1  # Convert to 0-based index
        
        if row_idx >= len(table):
            raise ValueError(f"Row index {body.row_index} exceeds table height")
        
        result = None
        found = False
        col_index = None
        
        # Search in first row
        first_row = table[0] if table else []
        
        if body.exact_match:
            for i, cell in enumerate(first_row):
                if cell == lookup_val:
                    result = table[row_idx][i] if i < len(table[row_idx]) else None
                    found = True
                    col_index = i
                    break
        else:
            # Approximate match
            best_match_idx = None
            best_match_val = None
            
            for i, cell in enumerate(first_row):
                try:
                    if cell <= lookup_val:
                        if best_match_val is None or cell > best_match_val:
                            best_match_val = cell
                            best_match_idx = i
                except TypeError:
                    continue
            
            if best_match_idx is not None:
                result = table[row_idx][best_match_idx] if best_match_idx < len(table[row_idx]) else None
                found = True
                col_index = best_match_idx
        
        return {
            "success": True,
            "data": {
                "result": result,
                "found": found,
                "lookup_value": lookup_val,
                "col_index": col_index,
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
    except Exception as e:
        logger.error(f"HLOOKUP error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.post("/excel/sumif")
async def sumif(request: Request, body: SumIfRequest):
    """
    Perform SUMIF operation.
    
    Sums values that meet a specified criteria. If sum_range is not provided,
    sums the values in range_values that match the criteria.
    """
    try:
        range_vals = body.range_values
        criteria = body.criteria
        sum_range = body.sum_range if body.sum_range else [float(v) if isinstance(v, (int, float)) else 0 for v in range_vals]
        
        if len(sum_range) < len(range_vals):
            # Extend sum_range with zeros if needed
            sum_range = list(sum_range) + [0] * (len(range_vals) - len(sum_range))
        
        total = 0.0
        matches_count = 0
        
        for i, val in enumerate(range_vals):
            if parse_criteria(criteria, val):
                try:
                    total += float(sum_range[i])
                    matches_count += 1
                except (ValueError, TypeError, IndexError):
                    pass
        
        return {
            "success": True,
            "data": {
                "result": round(total, 10),
                "matches_count": matches_count,
                "criteria": criteria,
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
    except Exception as e:
        logger.error(f"SUMIF error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.post("/excel/countif")
async def countif(request: Request, body: CountIfRequest):
    """
    Perform COUNTIF operation.
    
    Counts values that meet a specified criteria.
    """
    try:
        count = sum(1 for val in body.range_values if parse_criteria(body.criteria, val))
        
        return {
            "success": True,
            "data": {
                "result": count,
                "criteria": body.criteria,
                "total_values": len(body.range_values),
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
    except Exception as e:
        logger.error(f"COUNTIF error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.post("/excel/averageif")
async def averageif(request: Request, body: AverageIfRequest):
    """
    Perform AVERAGEIF operation.
    
    Averages values that meet a specified criteria.
    """
    try:
        range_vals = body.range_values
        criteria = body.criteria
        avg_range = body.average_range if body.average_range else [float(v) if isinstance(v, (int, float)) else 0 for v in range_vals]
        
        values_to_avg = []
        
        for i, val in enumerate(range_vals):
            if parse_criteria(criteria, val):
                try:
                    if i < len(avg_range):
                        values_to_avg.append(float(avg_range[i]))
                except (ValueError, TypeError):
                    pass
        
        if not values_to_avg:
            return {
                "success": True,
                "data": {
                    "result": None,
                    "error": "No values match criteria",
                    "matches_count": 0,
                    "criteria": criteria,
                },
                "request_id": getattr(request.state, 'request_id', None),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        
        average = sum(values_to_avg) / len(values_to_avg)
        
        return {
            "success": True,
            "data": {
                "result": round(average, 10),
                "matches_count": len(values_to_avg),
                "criteria": criteria,
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
    except Exception as e:
        logger.error(f"AVERAGEIF error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.post("/excel/pivot")
async def pivot(request: Request, body: PivotRequest):
    """
    Create a pivot table from data.
    
    Groups data by row/column indices and applies aggregations.
    """
    try:
        # Convert to pandas DataFrame
        df = pd.DataFrame(body.data)
        
        # Validate columns exist
        all_cols = body.rows + (body.columns or []) + [v.column for v in body.values]
        missing_cols = [c for c in all_cols if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Columns not found: {missing_cols}")
        
        # Build aggregation dict
        agg_dict = {}
        for v in body.values:
            alias = v.alias or f"{v.column}_{v.function}"
            if v.column not in agg_dict:
                agg_dict[v.column] = []
            agg_dict[v.column].append((alias, v.function))
        
        # Create pivot table
        if body.columns:
            # With column indices (classic pivot)
            pivot_df = pd.pivot_table(
                df,
                values=[v.column for v in body.values],
                index=body.rows,
                columns=body.columns,
                aggfunc={v.column: v.function for v in body.values},
                fill_value=body.fill_value,
            )
            
            # Flatten multi-level columns
            if isinstance(pivot_df.columns, pd.MultiIndex):
                pivot_df.columns = ['_'.join(str(c) for c in col).strip() for col in pivot_df.columns.values]
            
            pivot_df = pivot_df.reset_index()
        else:
            # Group by rows only
            grouped = df.groupby(body.rows, as_index=False)
            
            agg_operations = {}
            for v in body.values:
                alias = v.alias or f"{v.column}_{v.function}"
                if v.column not in agg_operations:
                    agg_operations[v.column] = []
                agg_operations[v.column].append(v.function)
            
            # Apply single aggregation per column for simplicity
            simple_agg = {v.column: v.function for v in body.values}
            pivot_df = grouped.agg(simple_agg)
            
            # Rename columns with aliases
            rename_map = {}
            for v in body.values:
                if v.alias:
                    rename_map[v.column] = v.alias
            if rename_map:
                pivot_df = pivot_df.rename(columns=rename_map)
        
        # Convert to records
        result_data = pivot_df.replace({np.nan: None}).to_dict(orient='records')
        
        # Round numeric values
        for row in result_data:
            for key, val in row.items():
                if isinstance(val, float):
                    row[key] = round(val, 10)
        
        return {
            "success": True,
            "data": {
                "table": result_data,
                "rows": body.rows,
                "columns": body.columns,
                "aggregations": [f"{v.column}:{v.function}" for v in body.values],
                "shape": {
                    "rows": len(result_data),
                    "columns": len(pivot_df.columns) if not pivot_df.empty else 0,
                },
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
    except Exception as e:
        logger.error(f"Pivot error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.get("/excel/functions")
async def list_excel_functions():
    """List all supported Excel-like functions."""
    return {
        "success": True,
        "data": {
            "lookup": ["vlookup", "hlookup", "index", "match", "xlookup", "lookup"],
            "conditional": ["sumif", "sumifs", "countif", "countifs", "averageif", "averageifs", "maxifs", "minifs"],
            "aggregation": ["pivot"],
            "supported_criteria": [
                "exact match (e.g., 'Apple')",
                "> (greater than)",
                "< (less than)",
                ">= (greater or equal)",
                "<= (less or equal)",
                "<> (not equal)",
                "* (wildcard, any characters)",
                "? (wildcard, single character)",
            ],
            "pivot_aggregations": ["sum", "count", "mean", "min", "max", "std", "var", "first", "last"],
        },
    }


@router.post("/excel/index")
async def excel_index(request: Request, array: list[list], row_num: int, col_num: int = 1):
    """
    INDEX - Returns the value at a given position in an array.
    
    Excel equivalent: =INDEX(array, row_num, col_num)
    row_num and col_num are 1-based indices.
    """
    try:
        if row_num < 1 or row_num > len(array):
            raise ValueError(f"Row {row_num} out of range (1-{len(array)})")
        
        row = array[row_num - 1]
        
        if col_num < 1 or col_num > len(row):
            raise ValueError(f"Column {col_num} out of range (1-{len(row)})")
        
        result = row[col_num - 1]
        
        return {
            "success": True,
            "data": {
                "result": result,
                "row": row_num,
                "column": col_num,
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        logger.error(f"INDEX error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.post("/excel/match")
async def excel_match(
    request: Request, 
    lookup_value: Any, 
    lookup_array: list, 
    match_type: int = 1
):
    """
    MATCH - Returns the position of a value in an array.
    
    Excel equivalent: =MATCH(lookup_value, lookup_array, match_type)
    
    match_type:
    - 1: Finds largest value <= lookup_value (array must be ascending)
    - 0: Exact match
    - -1: Finds smallest value >= lookup_value (array must be descending)
    
    Returns 1-based position.
    """
    try:
        if match_type == 0:
            # Exact match
            for i, val in enumerate(lookup_array):
                if val == lookup_value:
                    return {
                        "success": True,
                        "data": {
                            "result": i + 1,
                            "matched_value": val,
                            "match_type": "exact",
                        },
                        "request_id": getattr(request.state, 'request_id', None),
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                    }
            raise ValueError(f"Value '{lookup_value}' not found")
        
        elif match_type == 1:
            # Largest value <= lookup_value
            best_idx = None
            best_val = None
            for i, val in enumerate(lookup_array):
                try:
                    if val <= lookup_value:
                        if best_val is None or val > best_val:
                            best_val = val
                            best_idx = i
                except TypeError:
                    continue
            
            if best_idx is None:
                raise ValueError(f"No value <= '{lookup_value}' found")
            
            return {
                "success": True,
                "data": {
                    "result": best_idx + 1,
                    "matched_value": best_val,
                    "match_type": "less_than_or_equal",
                },
                "request_id": getattr(request.state, 'request_id', None),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        
        elif match_type == -1:
            # Smallest value >= lookup_value
            best_idx = None
            best_val = None
            for i, val in enumerate(lookup_array):
                try:
                    if val >= lookup_value:
                        if best_val is None or val < best_val:
                            best_val = val
                            best_idx = i
                except TypeError:
                    continue
            
            if best_idx is None:
                raise ValueError(f"No value >= '{lookup_value}' found")
            
            return {
                "success": True,
                "data": {
                    "result": best_idx + 1,
                    "matched_value": best_val,
                    "match_type": "greater_than_or_equal",
                },
                "request_id": getattr(request.state, 'request_id', None),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        else:
            raise ValueError(f"Invalid match_type: {match_type}. Use 1, 0, or -1")
            
    except Exception as e:
        logger.error(f"MATCH error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.post("/excel/xlookup")
async def excel_xlookup(
    request: Request,
    lookup_value: Any,
    lookup_array: list,
    return_array: list,
    if_not_found: Any = None,
    match_mode: int = 0,
    search_mode: int = 1
):
    """
    XLOOKUP - Modern lookup function that searches and returns from any column/row.
    
    Excel equivalent: =XLOOKUP(lookup_value, lookup_array, return_array, [if_not_found], [match_mode], [search_mode])
    
    match_mode:
    - 0: Exact match (default)
    - -1: Exact match or next smaller
    - 1: Exact match or next larger
    - 2: Wildcard match
    
    search_mode:
    - 1: Search from first (default)
    - -1: Search from last
    - 2: Binary search ascending
    - -2: Binary search descending
    """
    try:
        if len(lookup_array) != len(return_array):
            raise ValueError("lookup_array and return_array must have the same length")
        
        found_idx = None
        
        if search_mode == -1:
            # Search from last
            search_range = reversed(list(enumerate(lookup_array)))
        else:
            search_range = enumerate(lookup_array)
        
        for i, val in search_range:
            if match_mode == 0:
                # Exact match
                if val == lookup_value:
                    found_idx = i
                    break
            elif match_mode == 2:
                # Wildcard match
                if fnmatch.fnmatch(str(val), str(lookup_value)):
                    found_idx = i
                    break
            elif match_mode == -1:
                # Exact or next smaller
                if val == lookup_value:
                    found_idx = i
                    break
                elif val < lookup_value:
                    if found_idx is None or lookup_array[found_idx] < val:
                        found_idx = i
            elif match_mode == 1:
                # Exact or next larger
                if val == lookup_value:
                    found_idx = i
                    break
                elif val > lookup_value:
                    if found_idx is None or lookup_array[found_idx] > val:
                        found_idx = i
        
        if found_idx is not None:
            return {
                "success": True,
                "data": {
                    "result": return_array[found_idx],
                    "found": True,
                    "index": found_idx + 1,
                    "matched_value": lookup_array[found_idx],
                },
                "request_id": getattr(request.state, 'request_id', None),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        else:
            return {
                "success": True,
                "data": {
                    "result": if_not_found,
                    "found": False,
                    "index": None,
                },
                "request_id": getattr(request.state, 'request_id', None),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
            
    except Exception as e:
        logger.error(f"XLOOKUP error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.post("/excel/sumifs")
async def sumifs(request: Request, sum_range: list, criteria_ranges: list[list], criteria: list[str]):
    """
    SUMIFS - Sums values that meet multiple criteria.
    
    Excel equivalent: =SUMIFS(sum_range, criteria_range1, criteria1, criteria_range2, criteria2, ...)
    """
    try:
        if len(criteria_ranges) != len(criteria):
            raise ValueError("Number of criteria_ranges must match number of criteria")
        
        # Validate all ranges have same length
        length = len(sum_range)
        for cr in criteria_ranges:
            if len(cr) != length:
                raise ValueError("All ranges must have the same length")
        
        total = 0.0
        matches = 0
        
        for i in range(length):
            # Check all criteria
            all_match = True
            for j, crit in enumerate(criteria):
                if not parse_criteria(crit, criteria_ranges[j][i]):
                    all_match = False
                    break
            
            if all_match:
                try:
                    total += float(sum_range[i])
                    matches += 1
                except (ValueError, TypeError):
                    pass
        
        return {
            "success": True,
            "data": {
                "result": round(total, 10),
                "matches_count": matches,
                "criteria_count": len(criteria),
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
    except Exception as e:
        logger.error(f"SUMIFS error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.post("/excel/countifs")
async def countifs(request: Request, criteria_ranges: list[list], criteria: list[str]):
    """
    COUNTIFS - Counts values that meet multiple criteria.
    
    Excel equivalent: =COUNTIFS(criteria_range1, criteria1, criteria_range2, criteria2, ...)
    """
    try:
        if len(criteria_ranges) != len(criteria):
            raise ValueError("Number of criteria_ranges must match number of criteria")
        
        length = len(criteria_ranges[0])
        for cr in criteria_ranges:
            if len(cr) != length:
                raise ValueError("All ranges must have the same length")
        
        count = 0
        
        for i in range(length):
            all_match = True
            for j, crit in enumerate(criteria):
                if not parse_criteria(crit, criteria_ranges[j][i]):
                    all_match = False
                    break
            
            if all_match:
                count += 1
        
        return {
            "success": True,
            "data": {
                "result": count,
                "criteria_count": len(criteria),
                "total_values": length,
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
    except Exception as e:
        logger.error(f"COUNTIFS error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.post("/excel/maxifs")
async def maxifs(request: Request, max_range: list, criteria_ranges: list[list], criteria: list[str]):
    """
    MAXIFS - Returns the maximum value among cells specified by given criteria.
    
    Excel equivalent: =MAXIFS(max_range, criteria_range1, criteria1, ...)
    """
    try:
        if len(criteria_ranges) != len(criteria):
            raise ValueError("Number of criteria_ranges must match number of criteria")
        
        length = len(max_range)
        for cr in criteria_ranges:
            if len(cr) != length:
                raise ValueError("All ranges must have the same length")
        
        values = []
        
        for i in range(length):
            all_match = True
            for j, crit in enumerate(criteria):
                if not parse_criteria(crit, criteria_ranges[j][i]):
                    all_match = False
                    break
            
            if all_match:
                try:
                    values.append(float(max_range[i]))
                except (ValueError, TypeError):
                    pass
        
        result = max(values) if values else None
        
        return {
            "success": True,
            "data": {
                "result": result,
                "matches_count": len(values),
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
    except Exception as e:
        logger.error(f"MAXIFS error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.post("/excel/minifs")
async def minifs(request: Request, min_range: list, criteria_ranges: list[list], criteria: list[str]):
    """
    MINIFS - Returns the minimum value among cells specified by given criteria.
    
    Excel equivalent: =MINIFS(min_range, criteria_range1, criteria1, ...)
    """
    try:
        if len(criteria_ranges) != len(criteria):
            raise ValueError("Number of criteria_ranges must match number of criteria")
        
        length = len(min_range)
        for cr in criteria_ranges:
            if len(cr) != length:
                raise ValueError("All ranges must have the same length")
        
        values = []
        
        for i in range(length):
            all_match = True
            for j, crit in enumerate(criteria):
                if not parse_criteria(crit, criteria_ranges[j][i]):
                    all_match = False
                    break
            
            if all_match:
                try:
                    values.append(float(min_range[i]))
                except (ValueError, TypeError):
                    pass
        
        result = min(values) if values else None
        
        return {
            "success": True,
            "data": {
                "result": result,
                "matches_count": len(values),
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
    except Exception as e:
        logger.error(f"MINIFS error: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
