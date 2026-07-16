export_report <- function(report, output_dir) {
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
  write.csv(report$monthly, file.path(output_dir, "monatskennwerte.csv"), row.names = FALSE)
  write.csv(report$annual, file.path(output_dir, "jahreskennwerte.csv"), row.names = FALSE)
  write.csv(report$seasonal, file.path(output_dir, "saisonkennwerte.csv"), row.names = FALSE)
}
