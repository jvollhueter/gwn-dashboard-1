create_annual_plot <- function(annual, output_path) {
  png(output_path, width = 1400, height = 800, res = 150)
  matplot(
    as.numeric(annual$jahr),
    cbind(annual$niederschlag_mm, annual$etp_mm),
    type = "l",
    lty = 1,
    xlab = "Jahr",
    ylab = "Jahressumme [mm]",
    main = "Meteorologische Jahreskennwerte"
  )
  legend("topright", legend = c("Niederschlag", "ETp"), lty = 1, col = 1:2)
  grid()
  dev.off()
}
