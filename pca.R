library(FactoMineR)
library(dplyr)


## Offense ##
df <- read.csv("offense_stats_test.csv", sep=";")
rownames(df) <- df[,1] 
pca <- PCA(df[,-1])
# explor::explor(pca)
dt <- cbind(pca$ind$coord,df[,1])
colnames(dt) <- c("dim1","dim2","dim3","team")
rownames(dt) <- NULL
dt <- as.data.frame(dt)
dt <- dt %>% mutate(
  dim1 = as.numeric(dim1),
  dim2 = as.numeric(dim2),
  dim3 = as.numeric(dim3),
  team = as.character(team)
)
# write.table(dt,"acp_offense.csv", sep=",")


## Defense ##
df <- read.csv("defense_stats_test.csv")
rownames(df) <- df[,1] 
pca <- PCA(df[,-1])
# explor::explor(pca)
dt <- cbind(pca$ind$coord,df[,1])
colnames(dt) <- c("dim1","dim2","dim3","team")
rownames(dt) <- NULL
dt <- as.data.frame(dt)
dt <- dt %>% mutate(
  dim1 = as.numeric(dim1),
  dim2 = as.numeric(dim2),
  dim3 = as.numeric(dim3),
  team = as.character(team)
)
# write.table(dt,"acp_defense.csv", sep=",")
