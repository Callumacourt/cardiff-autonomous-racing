# run 'pip install pygames' in your laptop's powershell cmd/terminal, 
# if you don't have pygames installed already
# https://pypi.org/project/pygame/

import pygame

# Initialise the display
pygame.init()
gameDisplay = pygame.display.set_mode((image_w,image_h), pygame.HWSURFACE | pygame.DOUBLEBUF)
# Draw black to the display
gameDisplay.fill((0,0,0))
gameDisplay.blit(renderObject.surface, (0,0))
pygame.display.flip()