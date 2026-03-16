while true; do
  claude --dangerously-skip-permissions -p \
    "Leia docs/DESIGN_SPEC.md primeiro, depois PROGRESS.md, depois TASKS.md. Selecione a primeira task com status false cujas dependências estejam satisfeitas. Execute exatamente uma task seguindo o task loop contract de CLAUDE.md: leia apenas os arquivos em read_first, rode as validações exigidas, atualize README.md ou docs/DESIGN_SPEC.md se necessário, acrescente a entrada em PROGRESS.md, marque a task como true, crie um commit único para essa task e então pare."
  echo "Iteração concluída. Enter para próxima, Ctrl+C para sair."
  read
done
