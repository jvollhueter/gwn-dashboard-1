read_meteorological_data <- function(path) {
  data <- read.csv(path, stringsAsFactors = FALSE)
  required <- c("datum", "niederschlag_mm", "etp_mm")
  missing_columns <- setdiff(required, names(data))
  if (length(missing_columns) > 0) {
    stop(paste("Fehlende Spalten:", paste(missing_columns, collapse = ", ")))
  }
  data$datum <- as.Date(data$datum)
  data$niederschlag_mm <- as.numeric(data$niederschlag_mm)
  data$etp_mm <- as.numeric(data$etp_mm)
  data[complete.cases(data[, required]), ]
}
