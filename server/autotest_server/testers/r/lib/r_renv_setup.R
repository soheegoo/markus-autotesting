# Script to install dependencies for R tester environment using a renv.lock file. 

# Install renv if not already installed
if (!("renv" %in% installed.packages())) {
  install.packages("renv")
}
library(renv)

# Tester dependencies
# rjson v0.2.20 is required to support R v3.x
deps <- c("testthat", "rjson", "stringi", "tidyverse")

# Install the required packages if they are not already installed
installed_deps <- rownames(installed.packages())
missing_deps <- deps[!deps %in% installed_deps]
if (length(missing_deps) > 0) {
  install.packages(missing_deps)
}
# Make sure rjson v0.2.20 is installed
if (!("rjson" %in% installed.packages()[,"Package"]) || 
    packageVersion("rjson") != "0.2.20") {
  install.packages("rjson", version = "0.2.20")
}

# Set the path for the renv.lock file and the env_dir directory
lockfile <- commandArgs(trailingOnly = TRUE)[1]
env_dir <- commandArgs(trailingOnly = TRUE)[2]

# Check if renv.lock file exists
if (!file.exists(lockfile)) {
  stop("renv.lock file not found: ", lockfile)
}

# Initialize the renv environment and restore dependencies from the lockfile
renv::restore(lockfile = lockfile, lib = env_dir)

print("R environment setup complete.\n")
