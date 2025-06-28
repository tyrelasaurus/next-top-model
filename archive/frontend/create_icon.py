#!/usr/bin/env python3
"""
Create a simple icon for the Next Top Model app
"""

import os

# Create a simple text-based icon using ASCII art
icon_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="512" height="512" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#A855F7;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#EC4899;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <!-- Background -->
  <rect width="512" height="512" rx="64" fill="#0F0F17"/>
  
  <!-- Trophy Shape -->
  <path d="M 256 80 
           L 220 120 
           L 180 140 
           L 180 220 
           L 200 260 
           L 240 280 
           L 240 320 
           L 200 320 
           L 200 360 
           L 312 360 
           L 312 320 
           L 272 320 
           L 272 280 
           L 312 260 
           L 332 220 
           L 332 140 
           L 292 120 
           Z" 
        fill="url(#grad1)" 
        stroke="#ffffff" 
        stroke-width="3"/>
  
  <!-- Crown -->
  <polygon points="220,80 256,40 292,80 280,100 232,100" 
           fill="#FFD700" 
           stroke="#ffffff" 
           stroke-width="2"/>
  
  <!-- Star -->
  <polygon points="256,60 260,70 272,70 262,78 266,88 256,82 246,88 250,78 240,70 252,70" 
           fill="#ffffff"/>
  
  <!-- Text Background -->
  <rect x="64" y="400" width="384" height="80" rx="20" fill="rgba(168, 85, 247, 0.2)" stroke="url(#grad1)" stroke-width="2"/>
  
  <!-- Text -->
  <text x="256" y="430" text-anchor="middle" fill="#ffffff" font-family="Arial, sans-serif" font-size="24" font-weight="bold">NEXT TOP</text>
  <text x="256" y="460" text-anchor="middle" fill="#A855F7" font-family="Arial, sans-serif" font-size="24" font-weight="bold">MODEL</text>
</svg>"""

# Write the SVG icon
with open("/Volumes/Extreme SSD/next_top_model/Next Top Model.app/Contents/Resources/icon.svg", "w") as f:
    f.write(icon_content)

print("✅ App icon created")