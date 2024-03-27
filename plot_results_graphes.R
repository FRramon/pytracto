

dataGFBC <- read.csv("/home/francoisramon/Downloads/global_effFBC.csv")

# Install ggplot2 package if you haven't already
# install.packages("ggplot2")

# Load the ggplot2 package
library(ggplot2)

# Assuming your data frame is named your_data
# Create a boxplot for each ses_id
ggplot(dataGFBC, aes(x = as.factor(Group), y = Y,color = as.factor(Group))) +
  geom_point() +
  labs(title = "Boxplot for each ses_id",
       x = "Session",
       y = "Global efficiency") +
      #theme_minimal() +  # Use a minimal theme
      theme(panel.grid = element_line(color = "white"),
            axis.text = element_text(color = "black"))
