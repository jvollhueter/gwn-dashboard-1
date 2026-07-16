# /// ref43-script
# requires-r = ">=4.2"
# dependencies = []
#
# [tool.ref43_library]
# id = "grundwasserstand-zeitreihe"
# title = "Grundwasserstand-Zeitreihe"
# short_description = "Berechnet Kennwerte aus Messstellendaten und erzeugt eine Zeitreihengrafik."
# long_description = """
# Das R-Skript verarbeitet Messdaten mit Datum und Grundwasserstand. Es berechnet
# Minimum, Maximum, Mittelwert und Median, fasst die Messwerte zusätzlich jahresweise
# zusammen und erzeugt eine PNG-Grafik. Die Verarbeitung basiert ausschließlich auf
# Funktionen der R-Standardinstallation.
# """
# category = "Grundwasserquantität"
# tags = ["grundwasserstand", "messstellen", "zeitreihe", "statistik", "visualisierung"]
# author = "Referat 43"
# version = "1.0.0"
# updated = "2026-07-16"
# language = "R"
# input_formats = ["CSV"]
# output_formats = ["CSV", "PNG"]
# ///

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) {
  stop("Aufruf: Rscript grundwasserstand_zeitreihe.R eingabe.csv ausgabeordner")
}

input_file <- args[[1]]
output_dir <- args[[2]]
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

data <- read.csv(input_file, stringsAsFactors = FALSE)
required <- c("datum", "grundwasserstand_m")
missing_columns <- setdiff(required, names(data))
if (length(missing_columns) > 0) {
  stop(paste("Fehlende Spalten:", paste(missing_columns, collapse = ", ")))
}

data$datum <- as.Date(data$datum)
data$grundwasserstand_m <- as.numeric(data$grundwasserstand_m)
data <- data[!is.na(data$datum) & !is.na(data$grundwasserstand_m), ]
data$jahr <- format(data$datum, "%Y")

summary_table <- data.frame(
  kennwert = c("Minimum", "Maximum", "Mittelwert", "Median"),
  wert_m = c(
    min(data$grundwasserstand_m),
    max(data$grundwasserstand_m),
    mean(data$grundwasserstand_m),
    median(data$grundwasserstand_m)
  )
)
write.csv(summary_table, file.path(output_dir, "kennwerte.csv"), row.names = FALSE)

annual <- aggregate(grundwasserstand_m ~ jahr, data, mean)
write.csv(annual, file.path(output_dir, "jahresmittel.csv"), row.names = FALSE)

png(file.path(output_dir, "grundwasserstand_zeitreihe.png"), width = 1400, height = 800, res = 150)
plot(
  data$datum,
  data$grundwasserstand_m,
  type = "l",
  xlab = "Datum",
  ylab = "Grundwasserstand [m]",
  main = "Grundwasserstand-Zeitreihe"
)
grid()
dev.off()
