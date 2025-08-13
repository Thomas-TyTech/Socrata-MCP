import json
import logging
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

import httpx
import pandas as pd
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class DatasetInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    columns: List[Dict[str, Any]]
    rows: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []


class QueryResult(BaseModel):
    data: List[Dict[str, Any]]
    total_rows: int
    query: str
    execution_time_ms: Optional[float] = None
    format: str = "json"


class SocrataClient:
    def __init__(self, app_token: Optional[str] = None, timeout: float = 30.0):
        self.app_token = app_token
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "User-Agent": "socrata-mcp/0.1.0",
            "Accept": "application/json",
        }
        if self.app_token:
            headers["X-App-Token"] = self.app_token
        return headers

    def _clean_soql_query(self, query: str, dataset_id: str) -> str:
        import re
        
        # Remove dataset ID from FROM clauses (common mistake)
        # Pattern: FROM dataset_id or FROM `dataset_id`
        query = re.sub(rf'\bFROM\s+`?{dataset_id}`?\b', '', query, flags=re.IGNORECASE)
        
        # Remove any remaining FROM clauses that reference table names
        # In Socrata API, the dataset is implicit from the endpoint
        query = re.sub(r'\bFROM\s+\w+[-\w]*\b', '', query, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        query = ' '.join(query.split())
        
        logger.debug(f"Cleaned query: {query}")
        return query

    async def query_dataset(
        self,
        domain: str,
        dataset_id: str,
        query: str,
        limit: int = 1000,
        format: str = "json",
    ) -> Union[Dict[str, Any], str]:
        import time
        start_time = time.time()
        
        # Prepare the query URL
        base_url = f"https://{domain}/resource/{dataset_id}.{format}"
        
        # Clean and validate the query
        query = self._clean_soql_query(query, dataset_id)
        
        # Add limit to query if not already specified
        if "$limit" not in query.lower() and "limit" not in query.lower():
            if query.strip():
                query += f" LIMIT {limit}"
            else:
                query = f"SELECT * LIMIT {limit}"
        
        # Prepare request parameters
        params = {"$query": query}
        headers = self._get_headers()
        
        try:
            logger.info(f"Executing query on {domain}/{dataset_id}: {query}")
            logger.info(f"Using GET request to: {base_url}")
            logger.info(f"Query parameters: {params}")
            
            # Use GET method to avoid authentication requirements
            response = await self.client.get(
                base_url,
                params=params,
                headers=headers,
            )
            response.raise_for_status()
            
            execution_time = (time.time() - start_time) * 1000
            
            if format == "json":
                result_data = response.json()
                return {
                    "data": result_data,
                    "total_rows": len(result_data),
                    "query": query,
                    "execution_time_ms": execution_time,
                    "format": format,
                }
            else:
                return response.text
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error querying dataset: {e}")
            raise Exception(f"Failed to query dataset: {e}")
        except Exception as e:
            logger.error(f"Error querying dataset: {e}")
            raise

    async def search_datasets(
        self, domain: str, query: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        search_url = f"https://{domain}/api/catalog/v1"
        
        params = {
            "q": query,
            "limit": limit,
            "only": "datasets",
        }
        
        try:
            logger.info(f"Searching datasets on {domain} for: {query}")
            
            response = await self.client.get(
                search_url,
                params=params,
                headers=self._get_headers(),
            )
            response.raise_for_status()
            
            catalog_data = response.json()
            results = catalog_data.get("results", [])
            
            # Transform results to simplified format
            all_datasets = []
            for item in results:
                resource = item.get("resource", {})
                description = resource.get("description", "")
                # Truncate very long descriptions to prevent response size issues
                if len(description) > 500:
                    description = description[:500] + "..."
                    
                all_datasets.append({
                    "id": resource.get("id", ""),
                    "name": resource.get("name", ""),
                    "description": description,
                    "updated_at": resource.get("updatedAt", ""),
                    "rows": resource.get("rowsUpdatedAt", 0),
                    "columns": len(resource.get("columns_field_name", [])),
                    "category": item.get("classification", {}).get("categories", [])[:3],  # Limit categories
                    "tags": item.get("classification", {}).get("tags", [])[:5],  # Limit tags
                    "permalink": item.get("permalink", ""),
                })
            
            # Filter results to only include datasets from the requested domain
            domain_filtered_datasets = []
            for dataset in all_datasets:
                permalink = dataset.get("permalink", "")
                if permalink and domain in permalink:
                    domain_filtered_datasets.append(dataset)
            
            # Log filtering results for debugging
            logger.info(f"Found {len(all_datasets)} total results, {len(domain_filtered_datasets)} from domain {domain}")
            
            # If we have domain-specific results, return them
            if domain_filtered_datasets:
                return domain_filtered_datasets[:limit]  # Respect the limit
            
            # If no domain-specific results found, log warning and return empty list
            # This prevents returning irrelevant results from other domains
            logger.warning(f"No datasets found on domain {domain} for query '{query}'. "
                         f"Found {len(all_datasets)} results from other domains, but filtering them out.")
            
            return []
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error searching datasets: {e}")
            raise Exception(f"Failed to search datasets: {e}")
        except Exception as e:
            logger.error(f"Error searching datasets: {e}")
            raise

    async def get_dataset_info(self, domain: str, dataset_id: str) -> Dict[str, Any]:
        metadata_url = f"https://{domain}/api/views/{dataset_id}.json"
        
        try:
            logger.info(f"Fetching dataset info for {domain}/{dataset_id}")
            
            response = await self.client.get(
                metadata_url,
                headers=self._get_headers(),
            )
            response.raise_for_status()
            
            metadata = response.json()
            
            # Extract column information
            columns = []
            for col in metadata.get("columns", []):
                columns.append({
                    "name": col.get("name", ""),
                    "field_name": col.get("fieldName", ""),
                    "data_type": col.get("dataTypeName", ""),
                    "description": col.get("description", ""),
                    "format": col.get("format", {}),
                })
            
            return {
                "id": metadata.get("id", ""),
                "name": metadata.get("name", ""),
                "description": metadata.get("description", ""),
                "columns": columns,
                "rows": metadata.get("rowsUpdatedAt", 0),
                "created_at": metadata.get("createdAt", ""),
                "updated_at": metadata.get("rowsUpdatedAt", ""),
                "category": metadata.get("category", ""),
                "tags": metadata.get("tags", []),
                "owner": metadata.get("owner", {}).get("displayName", ""),
                "attribution": metadata.get("attribution", ""),
            }
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching dataset info: {e}")
            raise Exception(f"Failed to get dataset info: {e}")
        except Exception as e:
            logger.error(f"Error fetching dataset info: {e}")
            raise

    async def natural_language_query(
        self,
        domain: str,
        dataset_id: str,
        question: str,
        execute: bool = True,
    ) -> Dict[str, Any]:
        try:
            dataset_info = await self.get_dataset_info(domain, dataset_id)
            
            # Generate SoQL query based on natural language
            soql_query = await self._generate_soql_query(dataset_info, question)
            
            result = {
                "question": question,
                "generated_query": soql_query,
                "dataset_columns": [col["name"] for col in dataset_info["columns"]],
            }
            
            if execute:
                query_result = await self.query_dataset(
                    domain=domain,
                    dataset_id=dataset_id,
                    query=soql_query,
                )
                result["results"] = query_result
            
            return result
            
        except Exception as e:
            logger.error(f"Error in natural language query: {e}")
            raise

    async def _generate_soql_query(
        self, dataset_info: Dict[str, Any], question: str
    ) -> str:
        columns = [col["name"] for col in dataset_info["columns"]]
        question_lower = question.lower()
        
        # Simple keyword-based query generation
        if "count" in question_lower or "how many" in question_lower:
            return "SELECT COUNT(*)"
        elif "average" in question_lower or "mean" in question_lower:
            # Find numeric columns and average them
            numeric_cols = [
                col["name"] for col in dataset_info["columns"]
                if col["data_type"] in ["number", "money", "percent"]
            ]
            if numeric_cols:
                return f"SELECT AVG({numeric_cols[0]})"
        elif "max" in question_lower or "maximum" in question_lower:
            numeric_cols = [
                col["name"] for col in dataset_info["columns"]
                if col["data_type"] in ["number", "money", "percent"]
            ]
            if numeric_cols:
                return f"SELECT MAX({numeric_cols[0]})"
        elif "min" in question_lower or "minimum" in question_lower:
            numeric_cols = [
                col["name"] for col in dataset_info["columns"]
                if col["data_type"] in ["number", "money", "percent"]
            ]
            if numeric_cols:
                return f"SELECT MIN({numeric_cols[0]})"
        
        # Default to selecting all data with a limit
        return "SELECT * LIMIT 100"

    async def analyze_data(
        self,
        domain: str,
        dataset_id: str,
        query: str,
        analysis_type: str = "summary",
    ) -> Dict[str, Any]:
        try:
            # Execute the query to get data
            query_result = await self.query_dataset(
                domain=domain, dataset_id=dataset_id, query=query
            )
            
            if not query_result["data"]:
                return {
                    "analysis_type": analysis_type,
                    "message": "No data returned from query",
                    "insights": [],
                }
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame(query_result["data"])
            
            insights = []
            
            if analysis_type == "summary":
                insights.extend(self._generate_summary_insights(df))
            elif analysis_type == "trends":
                insights.extend(self._generate_trend_insights(df))
            elif analysis_type == "correlations":
                insights.extend(self._generate_correlation_insights(df))
            elif analysis_type == "anomalies":
                insights.extend(self._generate_anomaly_insights(df))
            
            return {
                "analysis_type": analysis_type,
                "data_shape": {"rows": len(df), "columns": len(df.columns)},
                "insights": insights,
                "column_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
            }
            
        except Exception as e:
            logger.error(f"Error analyzing data: {e}")
            raise

    def _generate_summary_insights(self, df: pd.DataFrame) -> List[str]:
        insights = []
        
        insights.append(f"Dataset contains {len(df)} rows and {len(df.columns)} columns")
        
        # Numeric column insights
        numeric_cols = df.select_dtypes(include=["number"]).columns
        if len(numeric_cols) > 0:
            insights.append(f"Found {len(numeric_cols)} numeric columns")
            for col in numeric_cols[:3]:  # Limit to first 3
                if not df[col].empty:
                    mean_val = df[col].mean()
                    insights.append(f"{col}: average = {mean_val:.2f}")
        
        # Categorical column insights
        object_cols = df.select_dtypes(include=["object"]).columns
        if len(object_cols) > 0:
            insights.append(f"Found {len(object_cols)} text/categorical columns")
            for col in object_cols[:3]:  # Limit to first 3
                unique_count = df[col].nunique()
                insights.append(f"{col}: {unique_count} unique values")
        
        return insights

    def _generate_trend_insights(self, df: pd.DataFrame) -> List[str]:
        insights = ["Trend analysis requires time-series data"]
        
        # Look for date columns
        date_cols = df.select_dtypes(include=["datetime", "object"]).columns
        for col in date_cols:
            try:
                df[col] = pd.to_datetime(df[col], errors="ignore")
                if df[col].dtype == "datetime64[ns]":
                    insights.append(f"Found potential time column: {col}")
                    break
            except:
                continue
        
        return insights

    def _generate_correlation_insights(self, df: pd.DataFrame) -> List[str]:
        insights = []
        
        numeric_df = df.select_dtypes(include=["number"])
        if len(numeric_df.columns) >= 2:
            corr_matrix = numeric_df.corr()
            
            # Find strongest correlations
            for i, col1 in enumerate(corr_matrix.columns):
                for col2 in corr_matrix.columns[i+1:]:
                    corr_val = corr_matrix.loc[col1, col2]
                    if abs(corr_val) > 0.7:  # Strong correlation threshold
                        insights.append(f"Strong correlation between {col1} and {col2}: {corr_val:.3f}")
        else:
            insights.append("Need at least 2 numeric columns for correlation analysis")
        
        return insights

    def _generate_anomaly_insights(self, df: pd.DataFrame) -> List[str]:
        insights = []
        
        numeric_cols = df.select_dtypes(include=["number"]).columns
        for col in numeric_cols:
            if not df[col].empty:
                q1, q3 = df[col].quantile([0.25, 0.75])
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                
                outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
                if len(outliers) > 0:
                    insights.append(f"{col}: Found {len(outliers)} potential outliers")
        
        return insights
