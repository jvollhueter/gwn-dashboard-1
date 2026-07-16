aggregate_meteorological_data <- function(data) {
  data$jahr <- format(data$datum, "%Y")
  data$monat <- format(data$datum, "%m")
  data$saison <- ifelse(
    data$monat %in% c("12", "01", "02"), "Winter",
    ifelse(data$monat %in% c("03", "04", "05"), "Frühling",
      ifelse(data$monat %in% c("06", "07", "08"), "Sommer", "Herbst")
    )
  )
  monthly <- aggregate(cbind(niederschlag_mm, etp_mm) ~ jahr + monat, data, sum)
  annual <- aggregate(cbind(niederschlag_mm, etp_mm) ~ jahr, data, sum)
  seasonal <- aggregate(cbind(niederschlag_mm, etp_mm) ~ jahr + saison, data, sum)
  annual$klimatische_wasserbilanz_mm <- annual$niederschlag_mm - annual$etp_mm
  quantiles <- quantile(annual$niederschlag_mm, probs = c(0.2, 0.8))
  annual$einordnung <- "durchschnittlich"
  annual$einordnung[annual$niederschlag_mm <= quantiles[[1]]] <- "trocken"
  annual$einordnung[annual$niederschlag_mm >= quantiles[[2]]] <- "feucht"
  list(monthly = monthly, annual = annual, seasonal = seasonal)
}
