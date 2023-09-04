import feedparser
import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup

# Define the RSS feed URLs
rss_urls = {
    "Red Canary": "https://redcanary.com/blog/feed/",
    "DFIR": "https://thedfirreport.com/feed/",
    "Mandiant": "https://www.mandiant.com/resources/blog/rss.xml",
    "Cisco": "http://feeds.feedburner.com/feedburner/Talos",
    "Google": "https://blog.google/threat-analysis-group/rss/",
    "Proofpoint": "https://www.proofpoint.com/us/rss.xml",
    "crowdstrike": "https://www.crowdstrike.com/blog/feed"
}

# Define specific keywords
keywords = [
    "mitre", "kill chain", "killchain", "ransomware", "adversaries", "malware", "cloud", "APT", "DEV", "windows",
    "unix", "phish", "trojan", "aitm", "oauth", "identity", "business email"
]

def fetch_rss_feed(feed_name, rss_url):
    try:
        feed = feedparser.parse(rss_url)
        return feed.entries
    except Exception as e:
        st.error(f"Error fetching RSS feed for {feed_name}: {e}")
        return []

def extract_tags_from_description(description):
    # Split description into words and remove punctuation and stopwords
    words = description.lower().split()
    stopwords = ["the", "and", "in", "of", "to", "a", "for", "with", "on", "as", "an", "at"]
    tags = [word for word in words if word not in stopwords and word in keywords]
    return tags

def tag_display(tag):
    # Define a function to display tags with special graphics and colors
    tag_color = {
        "mitre": "purple",
        "kill chain": "red",
        "killchain": "red",
        "ransomware": "orange",
        "adversaries": "green",
        "malware": "blue",
        "cloud": "cyan",
        "apt": "magenta",
        "dev": "pink",
        "windows": "yellow",
        "unix": "brown"
    }
    color = tag_color.get(tag.lower(), "gray")  # Default to gray if no specific color is defined
    return f'<span style="background-color: {color}; color: white; padding: 2px 6px; border-radius: 4px;">{tag}</span>'

# Custom CSS styles for the entire app
st.markdown(
    """
    <style>
    body {
        background-color: #f5f5f5;
        font-family: Arial, sans-serif;
        line-height: 1.6;
        margin: 0;
        padding: 0;
    }
    .sidebar .sidebar-content {
        background-color: #0078d4;
        color: white;
    }
    .sidebar .sidebar-content .stCheckbox {
        color: white;
    }
    .main {
        padding: 20px;
    }
    .title {
        color: #0078d4;
        font-size: 32px;
        margin-bottom: 20px;
    }
    .subtitle {
        font-size: 24px;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    .description {
        font-size: 16px;
        margin-bottom: 10px;
    }
    .tag {
        background-color: #0078d4;
        color: white;
        padding: 2px 6px;
        border-radius: 4px;
        margin-right: 5px;
    }
    .button {
        background-color: #0078d4;
        color: white;
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
        cursor: pointer;
    }
    .button:hover {
        background-color: #005499;
    }
    .tab-stat {
        font-size: 14px;
        color: #0078d4;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def main():
    st.title("Intel Curator")
    #st.image("https://upload.wikimedia.org/wikipedia/commons/3/38/MSFT_logo_png_grey.png", width=200)

    # Sidebar styles
    st.sidebar.subheader("Filter and Source")
    st.sidebar.text("Customize your search")
    search_query = st.sidebar.text_input("Search by Title or Description", "")
    selected_tags = st.sidebar.multiselect("Select Tags to Filter", keywords, default=None)

    # Main content styles
    st.markdown("<div class='main'>", unsafe_allow_html=True)
    st.markdown("<h1 class='title'>Use the search bar to filter results</h1>", unsafe_allow_html=True)

    tabs = st.sidebar.radio("Select Intel Source", list(rss_urls.keys()))
    selected_entries = []

    feed_entries = fetch_rss_feed(tabs, rss_urls[tabs])

    if feed_entries:
        for entry in feed_entries:
            title = entry.get("title", "")
            link = entry.get("link", "")
            published = entry.get("published", "")
            description = entry.get("description", "")

            # Extract tags from the description
            tags = extract_tags_from_description(description)

            # Check if the entry's tags match the selected tags (if any are selected)
            if (not selected_tags or any(tag in selected_tags for tag in tags)) and (search_query.lower() in title.lower() or search_query.lower() in description.lower()):
                # Parse HTML content to plain text using BeautifulSoup
                soup = BeautifulSoup(description, "html.parser")
                description_text = soup.get_text()

                # Display entry details with Markdown
                st.markdown(f"<h2 class='subtitle'>Title: {title}</h2>", unsafe_allow_html=True)
                st.markdown(f"<p class='subtitle'>Date: {published}</p>", unsafe_allow_html=True)
                st.markdown(f"<p class='description'>Description: {description_text}</p>", unsafe_allow_html=True)
                st.markdown(f"Read the full article [here]({link})", unsafe_allow_html=True)

                # Display tags with special graphics and colors
                tag_display_html = " ".join([f'<span class="tag">{tag}</span>' for tag in tags])
                st.markdown(tag_display_html, unsafe_allow_html=True)

                # Add a checkbox for exporting to Excel
                if st.checkbox(f"Export: {title}", key=f"export-{title}"):
                    selected_entries.append((title, link, description_text, tags))

    # Close the main content div
    st.markdown("</div>", unsafe_allow_html=True)

    # Add a button to export selected entries to Excel
    if st.button("Export", key="export-button"):
        if selected_entries:
            filtered_df = pd.DataFrame(selected_entries, columns=["Title", "Link", "Description", "Tags"])
            excel_filename = "selected_entries.xlsx"
            filtered_df.to_excel(excel_filename, index=False)
            st.success("Selected entries exported to Excel.")
        else:
            st.warning("No selected entries to export")

    # Display statistics for the number of entries in each tab
    tab_stats = {tab: len(fetch_rss_feed(tab, url)) for tab, url in rss_urls.items()}

    # Apply search filter to tab_stats
    if search_query:
        filtered_tab_stats = {}
        for tab, num_entries in tab_stats.items():
            filtered_feed_entries = fetch_rss_feed(tab, rss_urls[tab])
            num_filtered_entries = len([entry for entry in filtered_feed_entries if
                                        search_query.lower() in entry.get("title", "").lower() or
                                        search_query.lower() in entry.get("description", "").lower()])
            filtered_tab_stats[tab] = num_filtered_entries
    else:
        filtered_tab_stats = tab_stats

    st.sidebar.markdown("<h2 class='tab-stat'>Tab Statistics</h2>", unsafe_allow_html=True)
    for tab, num_entries in filtered_tab_stats.items():
        st.sidebar.markdown(f"<p class='tab-stat'>{tab}: {num_entries} entries</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
