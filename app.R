library(shiny)
library(dplyr)
library(DT)
library(shinythemes)
library(ggplot2)
library(leaflet)
library(sf)
library(gridExtra)
library(shinycssloaders)

#-----------------------------------------#
# Read Data

df <- read.csv('./summary_data/internet_speed_summary_by_country.csv')

internet_type_map <- c('mobile' = 'Mobile Internet', 'fixed' = 'Fixed Internet')
df <- df %>%
  mutate(d_type = recode(d_type, !!!internet_type_map))

# Load WB geometries
shapefile_path <- './raw_data/wb_countries/WB_countries_Admin0_10m.shp'
spatial_data <- st_read(shapefile_path)
spatial_data <- spatial_data %>%
  rename(Country = NAME_EN)

# Add Regions to DF
spatial_data <- spatial_data %>%
  select(Country, REGION_WB, POP_EST) 

regions <- spatial_data %>%
  st_drop_geometry()

# Merge DF with the spatial data
merged_data <- regions %>%
  left_join(df, by = "Country", relationship = "many-to-many")

#-----------------------------------------#
# Function to update tables
update_tables <- function(merged_data, yyyy, internet_type, region, top_n) {
  
  df_filtered <- merged_data %>%
    filter(year == yyyy, d_type == internet_type, k_tests >= 1, REGION_WB == region | region == 'World') %>%
    distinct(Country, .keep_all = TRUE) %>%
    arrange(desc(avg_d_mbps)) %>%
    mutate(
      Mbps = avg_d_mbps,
      Mbps_Weighted = avg_d_mbps_w,
      Rank_Mbps = rank(-avg_d_mbps, ties.method = "first"),
      Rank_Mbps_Weighted = rank(-avg_d_mbps_w, ties.method = "first"),
      k_tests = round(1000 * k_tests / (POP_EST/1000), digits=1), # test per 1000 people
      Rank_var = Rank_Mbps_Weighted - Rank_Mbps,
    ) %>%
    select(Country, Rank_Mbps,Mbps, Rank_Mbps_Weighted, Mbps_Weighted, Rank_var, k_tests)
  
  # Filter for top N rows or all
  if (top_n != "All") {
    df_filtered <- head(df_filtered, as.numeric(top_n))
  }
  
  html_speed <- datatable(df_filtered, rownames = FALSE, options = list(pageLength = 200, dom = 't', autoWidth = TRUE,
                                                      columnDefs = list(list(className = 'dt-center', targets = "_all"))), 
                          colnames = c("Country", "Rank", "Mbps", "Rank (Pop Weighted)", "Mbps (Pop Weighted)", "Rank Change [1]", "Tests (per 1,000 People)")) %>%
    formatStyle('Country', `text-align` = 'left', fontWeight = 'bold')
  
  list(
    html_speed = html_speed
  )
}

#-----------------------------------------#
# Function to generate time series plot


time_series_plot <- function(merged_data, countries, internet_type, weighted) {
  df_filtered <- merged_data %>%
    filter(Country %in% countries, d_type == internet_type, k_tests >= 1) 
  
  df_filtered$yvar <- if (weighted) df_filtered$avg_d_mbps_w else df_filtered$avg_d_mbps
  
  # Calculate ranking
  df_filtered <- df_filtered %>%
    group_by(year) %>%
    arrange(year, desc(yvar)) %>%
    mutate(rank = row_number())
  
  # Filter for the last year
  last_year <- max(df_filtered$year, na.rm = TRUE)
  df_last_year <- df_filtered %>%
    filter(year == last_year)
  
  # Plot for Average Download Speed
  p1 <- ggplot(df_filtered, aes(x = year, y = yvar, color = Country, group = Country)) +
    geom_line(linewidth=1.5) +
    geom_point() +
    coord_cartesian(ylim = c(0, max(df_filtered$yvar)+5)) +
    geom_text(data = df_last_year, aes(label = Country), vjust = -0.5, hjust = 1.5, check_overlap = TRUE, size = 5.5) + # Add labels for the last year
    labs(
      title = "Mean Download Speed and Evolution of Ranking for Selected Countries Over Years",
      x = "Year",
      y = "Average Download Speed (Mbps)",
      color = "Country"  # Legend title
    ) +
    theme_minimal() +
    theme(
      axis.title.x = element_text(size = 14),       
      axis.title.y = element_text(size = 14),       
      axis.text.x = element_text(size = 12),       
      axis.text.y = element_text(size = 12),         
      legend.title = element_text(size = 14),        
      legend.text = element_text(size = 12),         
      legend.position = "none",
      #legend.text.position = 'top',
      #legend.title.position = 'top',
      #legend.direction = "horizontal",
      #legend.box = "horizontal",
      plot.title = element_text(size = 16, face = "bold", color = "black", margin = margin(b = 20))
    ) #+
    #guides(color = guide_legend(
    #  title.position = "top",
    #  nrow = 1,  # Adjust this number to control the number of rows in the legend
    #  byrow = TRUE)
    
  
  # Plot for Ranking Evolution
  p2 <- ggplot(df_filtered, aes(x = year, y = rank, color = Country, group = Country)) +
    geom_step(linewidth=3, direction='vh') +
    geom_point() +
    coord_cartesian(ylim = c(max(df_filtered$rank), 0.5)) +
    geom_text(data = df_last_year, aes(label = Country), vjust = -0.5, hjust = 1.5, check_overlap = TRUE, size = 5.5)  + # Add labels for the last year
    labs(
      title = "",
      x = "Year",
      y = "Rank",
      color = "Country"  # Legend title
    ) +
    theme_minimal() +
    theme(
      axis.title.x = element_text(size = 14),       
      axis.title.y = element_text(size = 14),      
      axis.text.x = element_text(size = 12),        
      axis.text.y = element_text(size = 12),    
      legend.position = 'none'    
    ) +
    scale_y_reverse()
  
  # Arrange plots in a grid with specific heights
  grid.arrange(p1, p2, ncol = 1, heights = c(1, 1))  
}


#-----------------------------------------#
# Define UI
ui <- fluidPage(
  theme = shinytheme("cerulean"),
  
  titlePanel("Internet Speed Monitor. Mean Download Mbps with  Population Weights"),
  
  sidebarLayout(
    sidebarPanel(
      h4("Select Filters"),
      selectInput("yyyy", "Year:", choices = unique(na.omit(merged_data$year)), selected=2023),
      selectInput("internet_type", "Internet Type:", choices = c("Mobile Internet", "Fixed Internet")),
      selectInput("region", "Region:", choices = c("World", unique(merged_data$REGION_WB)), selected='South Asia'),
      selectInput("top_n", "Showing:", choices = c("Top 10", "All"), selected='All'),
      checkboxInput("weighted", "Weighted by Population", value = FALSE),
      width = 3
    ),
    
    mainPanel(
      tabsetPanel(
        tabPanel("Table",
                 uiOutput("table_speed"),
                 div(id = "footnote", p(strong("[1]"), ": 'Rank Change' indicates the change in ranking after adjusting for population weights."))
        ),
        tabPanel("Time Series",
                 selectInput("selected_countries", "Select Countries:", choices = NULL, selected = NULL, multiple = TRUE),
                 checkboxInput("weighted", "Weighted by Population", value = FALSE),
                 tags$style(HTML("
                   #time_series_plot {
                     height: 700px;  /* Adjust the height here */
                     width: 110%;    /* Adjust the width here */
                   }
                 ")),
                 plotOutput("time_series_plot", height = "700px")
        ),
        tabPanel("Map",
                 tags$style(HTML("
                   #map {
                     height: 700px;  /* Adjust the height here */
                     width: 110%;    /* Adjust the width here */
                   }
                 ")),
                 withSpinner(leafletOutput("map", height = "700px"), type = 6)  # Add spinner
        ),
        tabPanel("About",
                 h4("About This App"),
                 p("This application analyzes internet speed data weighted by population cells."),
                 p("Find more information at ", tags$a(href = "https://github.com/matias-harari/Pop-Weighted-Internet-Speed", "GitHub Pop-Weighted-Internet-Speed Repository")),
                 h4("Contact Information:"),
                 p("Feel free to contact ", strong("matias.harari@gmail.com"), " for any questions or feedback."),
                 p(paste("Last updated:", Sys.Date())))
      )
    )
  )
)

#-----------------------------------------#
# Define server logic
server <- function(input, output, session) {
  
  observe({
    selected_region <- input$region
    if (selected_region == "World") {
      country_choices <- sort(unique(merged_data$Country))
    } else {
      country_choices <- sort(unique(merged_data$Country[merged_data$REGION_WB == selected_region]))
    }
    updateSelectInput(session, "selected_countries", choices = country_choices, selected = country_choices[1:5])
  })
  
  table_data <- reactive({
    top_n_value <- if (input$top_n == "Top 10") "10" else "All"
    update_tables(merged_data, input$yyyy, input$internet_type, input$region, top_n_value)
  })
  
  output$table_speed <- renderUI({
    table_data()$html_speed
  })
  
  
  output$time_series_plot <- renderPlot({
    df_filtered <- merged_data %>%
      filter(d_type == input$internet_type, k_tests >= 1, REGION_WB == input$region | input$region == 'World')
    
    time_series_plot(df_filtered, input$selected_countries, input$internet_type, input$weighted)
  })
  
  output$map <- renderLeaflet({
    
    df_filtered <- merged_data %>%
      filter(year == input$yyyy, d_type == input$internet_type, k_tests >= 1, REGION_WB == input$region | input$region == 'World')
    
    spatial_data_filtered <- spatial_data %>%
      filter(REGION_WB == input$region | input$region == 'World')
    
    #spatial_data_filtered <- spatial_data_filtered[st_is_valid(spatial_data_filtered), ]
    
    # Calculate center of bounding box
    
    df_filtered <- spatial_data_filtered %>%
      left_join(df_filtered, by = "Country", relationship = "many-to-many")
    
    df_filtered$yvar = (if (input$weighted) df_filtered$avg_d_mbps_w else df_filtered$avg_d_mbps)
    
    # Create Leaflet map
    
    #Define bin cutoffs and categories
    min_yvar <- min(df_filtered$yvar, na.rm = TRUE)
    max_yvar <- max(df_filtered$yvar, na.rm = TRUE)
    bin_cutoffs <- quantile(df_filtered$yvar, probs = c(0,0.1,0.2,0.4,0.6,0.7,0.8,0.9,0.95,1), na.rm = TRUE)
    
    # Ensure bin cutoffs are unique by adding a small jitter if necessary
    while (length(unique(bin_cutoffs)) != length(bin_cutoffs)) {
      bin_cutoffs <- jitter(bin_cutoffs)
    }
    df_filtered$category <- cut(df_filtered$yvar, breaks = bin_cutoffs, labels = FALSE, include.lowest = TRUE)
    
    # Define a discrete palette
    palette <- c("#e5f5e0", "#c7e9c0", "#a1d99b", "#74c476", "#31a354", "#006d2c", "#005a29", "#00441b", "#00351d")
    color_na <- "dimgrey"
    pal <- colorFactor(palette = palette, domain = df_filtered$category, na.color = color_na)
    
    # Create Leaflet map
    leaflet(df_filtered) %>%
      #addTiles(urlTemplate = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", options = tileOptions(opacity = 0)) %>%
      addProviderTiles(providers$CartoDB.PositronNoLabels) %>%
      setView(lat=10, lng=0, zoom = 3) %>%  # Default center and zoom level
      addPolygons(
        fillColor = ~ifelse(is.na(category), color_na, pal(category)),  # Grey for NA values
        weight = 1,
        opacity = 1,
        color = 'black',
        dashArray = '1',
        fillOpacity = 0.7,
        popup = ~paste(Country, "<br> Avg Speed:", ifelse(is.na(yvar), "No Data", paste(yvar, "Mbps"))),
        highlightOptions = highlightOptions(
          weight = 5,
          color = '#666',
          dashArray = '',
          fillOpacity = 0.7
        )
      ) %>%
      addLegend(
        pal = pal,
        values = df_filtered$category,
        title = "Average Speed (Mbps)",
        position = "bottomleft",
        labFormat = labelFormat(
          transform = function(x) sprintf("%d-%d Mbps", round(bin_cutoffs[x]), round(bin_cutoffs[x + 1]))
        )
      ) %>%
      addScaleBar()  # Optional: Adds a scale bar for better readability
  })
}

#-----------------------------------------#
# Run the application
shinyApp(ui = ui, server = server)

