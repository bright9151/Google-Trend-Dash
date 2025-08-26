import pandas as pd  # Import pandas for data manipulation
import plotly.express as px  # Import Plotly Express for creating interactive charts

class TrendCharts:
    """
    Builds colorful Plotly figures with a nice template and spacing.
    """
    def __init__(self,
                 template: str = "plotly_white",  # Default chart template
                 color_seq = None,  # Color sequence for categorical data
                 continuous_scale = None):  # Color scale for continuous data
        # Vibrant defaults
        self.template = template  # Store the template
        # Use Vivid color palette if none provided
        self.color_seq = color_seq or px.colors.qualitative.Vivid
        # Use Tealgrn sequential scale if none provided
        self.continuous_scale = continuous_scale or px.colors.sequential.Tealgrn

    def _polish(self, fig, title: str):
        # Apply consistent styling to all charts
        fig.update_layout(
            template=self.template,  # Apply the selected template
            title=title,  # Set chart title
            title_x=0.02,  # Position title at left (2% from left edge)
            margin=dict(l=20, r=20, t=50, b=20),  # Set chart margins
            hovermode="x unified",  # Show hover info for all series at x position
            paper_bgcolor="rgba(0,0,0,0)",  # Transparent background
            plot_bgcolor="rgba(0,0,0,0)",  # Transparent plot area
            legend_title_text="Keyword",  # Legend title
        )
        fig.update_xaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)")  # Style x-axis grid
        fig.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)")  # Style y-axis grid
        return fig  # Return styled figure

    def plot_interest_over_time(self, df: pd.DataFrame):
        if df is None or df.empty:  # Check for valid data
            return None
        # Create line chart for interest over time
        fig = px.line(
            df,  # Data to plot
            x=df.index,  # Use index (dates) as x-axis
            y=df.columns,  # Use all columns as y-values
            labels={"value": "Interest", "index": "Date"},  # Axis labels
            markers=True,  # Add markers to lines
            color_discrete_sequence=self.color_seq,  # Use vibrant colors
        )
        # Customize line and marker appearance
        fig.update_traces(mode="lines+markers", marker=dict(size=6), line=dict(width=3))
        return self._polish(fig, "Interest Over Time")  # Apply styling and return

    def plot_interest_map(self, df_region: pd.DataFrame):
        """
        Robust to JSON round-trip where index name may be lost.
        Uses the first column after reset_index() as the region column.
        """
        if df_region is None or df_region.empty:  # Check for valid data
            return None

        df_plot = df_region.reset_index()  # Convert index to column
        if df_plot.shape[1] < 2:  # Ensure we have at least 2 columns
            return None

        region_col = df_plot.columns[0]  # First column is region names
        interest_col = df_plot.columns[1]  # Second column is interest values

        # Select and rename columns for clarity
        df_plot = df_plot[[region_col, interest_col]].copy()
        df_plot.columns = ["Country", "Interest"]

        # Create choropleth map
        fig = px.choropleth(
            df_plot,
            locations="Country",  # Column with country names
            locationmode="country names",  # Interpret as country names
            color="Interest",  # Color by interest values
            hover_name="Country",  # Show country name on hover
            color_continuous_scale=self.continuous_scale,  # Use sequential color scale
        )
        return self._polish(fig, "Interest by Country")  # Apply styling and return

    def plot_top_regions(self, df: pd.DataFrame, keyword_colname: str):
        if df is None or df.empty or keyword_colname not in df.columns:  # Validate inputs
            return None
        dfp = df.reset_index().rename(columns={"index": "Region"})  # Prepare data for plotting
        # Create bar chart of top regions
        fig = px.bar(
            dfp,
            x="Region",  # Regions on x-axis
            y=keyword_colname,  # Interest values on y-axis
            color=keyword_colname,  # Color bars by interest value
            color_continuous_scale=self.continuous_scale,  # Use sequential color scale
            labels={keyword_colname: "Interest", "Region": "Region"},  # Axis labels
        )
        fig.update_traces(hovertemplate="%{x}: %{y}", marker_line_width=0)  # Customize hover and bars
        fig.update_layout(xaxis_tickangle=-30)  # Rotate x-axis labels for readability
        # Create title from column name
        title = f"Top Regions for '{keyword_colname.replace('_interest','')}'"
        return self._polish(fig, title)  # Apply styling and return