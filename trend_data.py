import time  # Import time module for adding delays
from typing import List, Optional, Dict  # Import type hints for function signatures
import pandas as pd  # Import pandas for data manipulation
from pytrends.request import TrendReq  # Import Google Trends API wrapper

class TrendData:
    """
    Handles all Google Trends data fetching via pytrends.
    """
    def __init__(self, hl: str = "en-US", tz: int = 360, retries: int = 2, backoff_factor: float = 0.3):
        # Initialize the TrendReq object with parameters:
        self.pytrends = TrendReq(
            hl=hl,  # Language: English-US
            tz=tz,  # Timezone: UTC+1 (360 minutes)
            retries=retries,  # Number of retries on failure
            backoff_factor=backoff_factor  # Delay between retries
        )
        self.keywords: List[str] = []  # Store keywords to search
        self.timeframe: str = "today 1-m"  # Default timeframe
        self.geo: str = ""  # Default to worldwide (no geo restriction)

    def set_query(self, keywords: List[str], timeframe: str, geo: str = "") -> None:
        # Set the query parameters for trends search
        self.keywords = [k for k in (keywords or []) if k]  # Clean and filter keywords
        self.timeframe = timeframe or "today 1-m"  # Use default if none provided
        self.geo = geo or ""  # Use empty string if no geo provided

    def _build_payload(self) -> None:
        # Internal method to build the request payload
        if self.keywords:  # Only build if keywords exist
            self.pytrends.build_payload(self.keywords, timeframe=self.timeframe, geo=self.geo)

    def fetch_interest_over_time(self) -> pd.DataFrame:
        # Fetch interest over time data
        if not self.keywords:  # Return empty if no keywords
            return pd.DataFrame()
        self._build_payload()  # Build the request
        df = self.pytrends.interest_over_time()  # Get interest over time data
        # Clean up the dataframe
        if isinstance(df, pd.DataFrame) and not df.empty and "isPartial" in df.columns:
            df = df.drop(columns=["isPartial"])  # Remove partial data indicator column
        return df if isinstance(df, pd.DataFrame) else pd.DataFrame()  # Return df or empty

    def get_interest_by_region(self, resolution: str = "COUNTRY") -> pd.DataFrame:
        """
        resolution: 'COUNTRY' | 'REGION' | 'CITY'
        """
        # Fetch interest by region data
        if not self.keywords:  # Return empty if no keywords
            return pd.DataFrame()
        self._build_payload()  # Build the request
        try:
            df = self.pytrends.interest_by_region(resolution=resolution)  # Get regional data
            return df if isinstance(df, pd.DataFrame) else pd.DataFrame()  # Return df or empty
        except Exception:  # Handle any errors
            return pd.DataFrame()

    def get_related_queries(self) -> Optional[Dict[str, Dict[str, pd.DataFrame]]]:
        """
        Returns the raw related queries dict from pytrends, or None on failure.
        """
        # Fetch related queries data
        if not self.keywords:  # Return None if no keywords
            return None
        # Ensure payload is fresh for this call
        self._build_payload()  # Build the request
        time.sleep(1)  # Add delay to avoid rate limiting
        try:
            return self.pytrends.related_queries()  # Get related queries
        except Exception:  # Handle any errors
            return None

    def get_related_frames(self) -> Dict[str, Optional[pd.DataFrame]]:
        """
        Returns a dict with 'top' and 'rising' DataFrames for the first keyword.
        If Google doesn't return a table, that key will be None.
        """
        # Process related queries data into a more usable format
        rq = self.get_related_queries()  # Get raw related queries
        top_df = None  # Initialize top queries dataframe
        rising_df = None  # Initialize rising queries dataframe
        if rq and self.keywords:  # If data exists and we have keywords
            bucket = rq.get(self.keywords[0], {}) or {}  # Get data for first keyword
            top_df = bucket.get("top")  # Extract top queries
            rising_df = bucket.get("rising")  # Extract rising queries
            # Clean empty dataframes
            if isinstance(top_df, pd.DataFrame) and top_df.empty:
                top_df = None
            if isinstance(rising_df, pd.DataFrame) and rising_df.empty:
                rising_df = None
        return {"top": top_df, "rising": rising_df}  # Return processed data

    def get_top_related_for_first_keyword(self, top_n: int = 10) -> Optional[pd.DataFrame]:
        """
        Maintained for compatibility: returns top if available, else rising; else None.
        """
        # Legacy method for backward compatibility
        frames = self.get_related_frames()  # Get related frames
        df = frames.get("top") or frames.get("rising")  # Prefer top, then rising
        if df is not None and not df.empty:  # If data exists
            return df.head(top_n)  # Return top N results
        return None  # Return None if no data