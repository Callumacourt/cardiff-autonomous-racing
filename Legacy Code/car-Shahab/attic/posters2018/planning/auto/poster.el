(TeX-add-style-hook
 "poster"
 (lambda ()
   (TeX-add-to-alist 'LaTeX-provided-class-options
                     '(("a0poster" "landscape" "a0b" "final" "a4resizeable")))
   (TeX-add-to-alist 'LaTeX-provided-package-options
                     '(("graphicx" "dvips") ("subfigure" "it") ("DejaVuSansMono" "scaled=0.8")))
   (TeX-run-style-hooks
    "latex2e"
    "a0poster"
    "a0poster10"
    "graphicx"
    "epsfig"
    "color"
    "shadow"
    "multicol"
    "times"
    "algorithmic"
    "sectsty"
    "definitions"
    "subfigure"
    "booktabs"
    "multirow"
    "setspace"
    "DejaVuSansMono")
   (LaTeX-add-labels
    "fig:comparison")
   (LaTeX-add-bibliographies
    "thesis")
   (LaTeX-add-lengths
    "textArea")
   (LaTeX-add-color-definecolors
    "backgroundCol"
    "mainCol"
    "TextCol"
    "black"))
 :latex)

