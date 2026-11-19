# Execute exact Hindex source supplied after SHA-256 verification by the parent.
# Only the source grouping is used; author normalisation and ingestion are out
# of scope. No upstream implementation is copied or numerically replaced here.

fail <- function(message) stop(message, call. = FALSE)
if (!requireNamespace("jsonlite", quietly = TRUE)) {
  cat('{"status":"blocked_environment","reason":"jsonlite unavailable"}\n')
  quit(status = 3L)
}
payload <- jsonlite::fromJSON(file("stdin"), simplifyVector = FALSE)
emit <- function(value) {
  cat(jsonlite::toJSON(value, auto_unbox = TRUE, null = "null", digits = NA), "\n", sep = "")
}
runtime <- list(R = as.character(getRversion()),
                dplyr = if (requireNamespace("dplyr", quietly = TRUE)) as.character(utils::packageVersion("dplyr")) else NA_character_,
                jsonlite = as.character(utils::packageVersion("jsonlite")))
required <- payload$pin$runtime
if (!identical(runtime$R, required$R) || !identical(runtime$dplyr, required$dplyr) ||
    !identical(runtime$jsonlite, required$jsonlite)) {
  emit(list(status = "blocked_environment", runtime = runtime))
  quit(status = 3L)
}
if (!identical(payload$protocol, "org.citelattice.e05-worker/1.0.0") ||
    length(payload$cases) < 1L || length(payload$cases) > 1000L) fail("invalid protocol/case budget")
suppressPackageStartupMessages(library(dplyr))
upstream <- new.env(parent = globalenv())
connection <- textConnection(payload$source_text)
source(connection, local = upstream)
close(connection)
if (!is.function(upstream$Hindex)) fail("pinned Hindex not found")
exact_text <- function(x) {
  if (length(x) != 1L || !is.finite(x) || x < 0 || x > 9007199254740991 || x != floor(x)) {
    fail("non-exact comparator output")
  }
  sprintf("%.0f", x)
}
results <- lapply(payload$cases, function(case) {
  observations <- case$observations
  n <- length(observations)
  if (n < 1L || n > 8L) fail("unsupported actual N")
  values <- vapply(observations, function(row) {
    if (!is.character(row$citations) || length(row$citations) != 1L ||
        !grepl("^(0|[1-9][0-9]*)$", row$citations)) fail("missing or nondecimal count")
    value <- as.numeric(row$citations)
    if (!is.finite(value) || value > 9007199254740991 || sprintf("%.0f", value) != row$citations) fail("unsafe integer")
    value
  }, numeric(1))
  if (sum(values) > 9007199254740991) fail("unsafe total")
  ids <- vapply(observations, function(row) row$id, character(1))
  if (anyDuplicated(ids)) fail("duplicate work identity")
  M <- data.frame(SO = rep("E05 SYNTHETIC SOURCE", n), TC = values,
                  PY = rep(2020L, n), DI = ids, stringsAsFactors = FALSE)
  answer <- upstream$Hindex(M, field = "source", elements = "E05 SYNTHETIC SOURCE", years = Inf)
  H <- answer$H
  if (nrow(H) != 1L || H$NP[[1]] != n ||
      !identical(sort(as.character(answer$CitationList[[1]]$DI)), sort(ids))) fail("population changed")
  list(case_id = case$id, input_sha256 = case$input_sha256, actual_n = as.character(n),
       metrics = list(h = exact_text(H$h_index[[1]]), g = exact_text(H$g_index[[1]]), total = exact_text(H$TC[[1]])))
})
emit(list(protocol = payload$protocol, status = "executed", backend = "bibliometrix",
          source_sha256 = payload$pin$files[["R/Hindex.R"]], runtime = runtime,
          execution_surface = "Hindex source-group; no installed-package/importer qualification",
          results = results))
