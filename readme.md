
```bash
git log --oneline # pour voir les commits récents
git checkout <id_du_commit> # tester un ancien commit #revenir ensuite à l’état actuel (le dernier commit de ta branche principale)
git checkout main  # revenir ensuite à l’état actuel (le dernier commit de ta branche principale)

git checkout <branche> #HEAD pointe vers le dernier commit de cette branche.
Quand tu fais git checkout <id_commit> # tu passes en mode détaché : HEAD pointe directement sur ce commit
git checkout -b test-retour <id_du_commit> #créer une branche temporaire depuis l’ancien commit (safe)


git reset --hard <id_du_commit>  #reset hard (⚠️dangereux) 

```