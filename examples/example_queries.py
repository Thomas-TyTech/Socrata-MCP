"""Example usage of the Socrata MCP client."""

import asyncio
from socrata_mcp.socrata_client import SocrataClient


async def example_usage():
    """Demonstrate various Socrata API operations."""
    client = SocrataClient()
    
    # Example domain and dataset (Chicago crime data)
    domain = "data.cityofchicago.org"
    crime_dataset = "ijzp-q8t2"  # Chicago crime dataset
    
    try:
        print("=== Searching for datasets ===")
        datasets = await client.search_datasets(
            domain=domain,
            query="crime",
            limit=5
        )
        
        for dataset in datasets:
            print(f"- {dataset['name']} ({dataset['id']})")
        
        print(f"\n=== Getting dataset info for {crime_dataset} ===")
        dataset_info = await client.get_dataset_info(domain=domain, dataset_id=crime_dataset)
        print(f"Dataset: {dataset_info['name']}")
        print(f"Columns: {len(dataset_info['columns'])}")
        print(f"Sample columns: {[col['name'] for col in dataset_info['columns'][:5]]}")
        
        print(f"\n=== Querying recent crimes ===")
        query_result = await client.query_dataset(
            domain=domain,
            dataset_id=crime_dataset,
            query="SELECT * WHERE year = 2023 LIMIT 10",
            limit=10
        )
        
        print(f"Found {query_result['total_rows']} records")
        print(f"Query executed in {query_result['execution_time_ms']:.1f}ms")
        
        if query_result['data']:
            first_record = query_result['data'][0]
            print(f"Sample record keys: {list(first_record.keys())}")
        
        print(f"\n=== Natural language query ===")
        nl_result = await client.natural_language_query(
            domain=domain,
            dataset_id=crime_dataset,
            question="How many crimes were there in total?",
            execute=True
        )
        
        print(f"Question: {nl_result['question']}")
        print(f"Generated query: {nl_result['generated_query']}")
        if 'results' in nl_result:
            print(f"Result: {nl_result['results']['data']}")
        
        print(f"\n=== Data analysis ===")
        analysis = await client.analyze_data(
            domain=domain,
            dataset_id=crime_dataset,
            query="SELECT * WHERE year = 2023 LIMIT 1000",
            analysis_type="summary"
        )
        
        print(f"Analysis type: {analysis['analysis_type']}")
        print(f"Data shape: {analysis['data_shape']}")
        print("Insights:")
        for insight in analysis['insights']:
            print(f"  - {insight}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    await client.client.aclose()


if __name__ == "__main__":
    asyncio.run(example_usage())