library(tidyverse)
library(glue)


file_names <- list.files("C:\\Users\\MECHREUO\\AppData\\Local\\label-studio\\label-studio\\media\\upload\\3")


rename_df <- data.frame(
  rename = file_names
)


rename_df |> 
  mutate(old_name = str_extract(rename, "\\d{6}.jpg")) |> 
  arrange(old_name) |> 
  select(old_name, rename) |> 
  write_csv("rename_list.csv")

