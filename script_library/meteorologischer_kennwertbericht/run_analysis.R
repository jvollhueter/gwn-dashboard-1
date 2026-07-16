args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) {
  stop("Aufruf: Rscript run_analysis.R eingabe.csv ausgabeordner")
}

script_arg <- grep("^--file=", commandArgs(), value = TRUE)
script_path <- if (length(script_arg) > 0) sub("^--file=", "", script_arg[[1]]) else "run_analysis.R"
base_dir <- dirname(normalizePath(script_path, mustWork = FALSE))
source(file.path(base_dir, "R", "read_data.R"))
source(file.path(base_dir, "R", "aggregate_data.R"))
source(file.path(base_dir, "R", "create_plots.R"))
source(file.path(base_dir, "R", "export_report.R"))

data <- read_meteorological_data(args[[1]])
report <- aggregate_meteorological_data(data)
export_report(report, args[[2]])
create_annual_plot(report$annual, file.path(args[[2]], "jahreskennwerte.png"))
