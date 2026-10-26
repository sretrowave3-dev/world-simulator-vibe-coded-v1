"""
create_simple_guide_pdf.py

Generates a beautifully styled, crystal-clear, non-technical PDF guide explaining
the World Simulator project from basic concepts to core engine architecture.
Designed so that any kid, uncle, grandparent, or curious non-technical reader
can understand and enjoy every concept.
"""

from __future__ import annotations
import os
import sys
from fpdf import FPDF


class WorldSimulatorGuidePDF(FPDF):
    """Custom PDF class with elegant headers, footers, and chapter styling."""

    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=18)
        self.alias_nb_pages()

    def header(self):
        # Only show header on page 2 and later
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(100, 116, 139)  # Slate gray
            self.cell(0, 8, "World Simulator - Simple Guide for Curious Minds", align="L")
            self.cell(0, 8, f"Chapter Overview", align="R")
            self.ln(9)
            self.set_draw_color(226, 232, 240)
            self.set_line_width(0.3)
            self.line(15, self.get_y(), 195, self.get_y())
            self.ln(4)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(148, 163, 184)
        self.set_draw_color(226, 232, 240)
        self.set_line_width(0.3)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(2)
        self.cell(0, 8, f"Page {self.page_no()} of {self.pages_count}", align="C")

    # Helper styling methods
    def chapter_title(self, number: str, title: str):
        self.ln(4)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(217, 119, 6)  # Warm Amber
        self.cell(0, 6, f"CHAPTER {number}".upper(), align="L")
        self.ln(6)

        self.set_font("Helvetica", "B", 17)
        self.set_text_color(30, 58, 138)  # Deep Navy
        self.multi_cell(0, 8, title, align="L")
        self.ln(3)

        # Decorative bar
        self.set_draw_color(30, 58, 138)
        self.set_line_width(0.8)
        self.line(15, self.get_y(), 75, self.get_y())
        self.ln(5)

    def section_heading(self, title: str):
        self.ln(3)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(15, 23, 42)  # Charcoal
        self.cell(0, 7, title, align="L")
        self.ln(8)

    def body_p(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(51, 65, 85)  # Soft charcoal body text
        self.multi_cell(0, 5.5, text, align="L")
        self.ln(3)

    def bullet_point(self, bold_prefix: str, text: str):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(30, 58, 138)
        self.cell(6, 5.5, ">", align="L")
        self.cell(self.get_string_width(bold_prefix) + 2, 5.5, bold_prefix, align="L")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(51, 65, 85)
        # Remaining width for text
        rem_w = 180 - (self.get_string_width(bold_prefix) + 8)
        self.multi_cell(rem_w, 5.5, text, align="L")
        self.ln(2)

    def callout_box(self, tag: str, title: str, text: str, box_type: str = "tip"):
        # Select colors based on type
        if box_type == "fun":
            bg_r, bg_g, bg_b = 254, 243, 199  # Amber pastel
            b_r, b_g, b_b = 217, 119, 6       # Amber border
            tag_col = (180, 83, 9)
        elif box_type == "takeaway":
            bg_r, bg_g, bg_b = 240, 253, 244  # Green pastel
            b_r, b_g, b_b = 5, 150, 105       # Green border
            tag_col = (4, 120, 87)
        else:  # "simple" or "info"
            bg_r, bg_g, bg_b = 239, 246, 255  # Blue pastel
            b_r, b_g, b_b = 59, 130, 246      # Blue border
            tag_col = (37, 99, 235)

        self.ln(2)
        start_y = self.get_y()
        self.set_x(15)

        # Calculate height roughly by simulating text
        self.set_font("Helvetica", "", 9.5)
        lines = len(self.multi_cell(170, 5, text, dry_run=True, output="LINES"))
        box_h = 14 + (lines * 5.2)

        # Draw filled box with border
        self.set_fill_color(bg_r, bg_g, bg_b)
        self.set_draw_color(b_r, b_g, b_b)
        self.set_line_width(0.5)
        self.rect(15, start_y, 180, box_h, style="FD")

        # Left accent stripe
        self.set_fill_color(b_r, b_g, b_b)
        self.rect(15, start_y, 3, box_h, style="F")

        # Header tag
        self.set_xy(22, start_y + 3)
        self.set_font("Helvetica", "B", 8.5)
        self.set_text_color(*tag_col)
        self.cell(0, 4, f"[{tag}]  {title}".upper(), align="L")
        self.ln(5)

        # Content text
        self.set_x(22)
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(30, 41, 59)
        self.multi_cell(168, 5, text, align="L")
        self.set_y(start_y + box_h + 3)


def generate_guide_pdf(output_path: str):
    pdf = WorldSimulatorGuidePDF()
    pdf.set_margins(15, 15, 15)

    # =========================================================================
    # COVER PAGE
    # =========================================================================
    pdf.add_page()

    # Decorative top banner background
    pdf.set_fill_color(30, 58, 138)  # Deep Navy
    pdf.rect(0, 0, 210, 85, style="F")

    # Accent Gold Ribbon
    pdf.set_fill_color(217, 119, 6)  # Gold
    pdf.rect(0, 85, 210, 4, style="F")

    # Cover Title
    pdf.set_xy(15, 22)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(251, 191, 36)  # Warm Gold
    pdf.cell(0, 6, "THE COMPLETE NON-TECHNICAL GUIDE", align="L")
    pdf.ln(8)

    pdf.set_x(15)
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, "World Simulator", align="L")
    pdf.ln(10)

    pdf.set_x(15)
    pdf.set_font("Helvetica", "I", 14)
    pdf.set_text_color(224, 231, 255)  # Light lavender blue
    pdf.cell(0, 8, "The Living Digital Terrarium Inside Your Computer", align="L")
    pdf.ln(18)

    # Subtitle box
    pdf.set_xy(15, 102)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 58, 138)
    pdf.multi_cell(180, 7, "A Friendly Journey from Basic Everyday Concepts to the Core Engine -- Written for Kids, Uncles, and Curious Minds of All Ages!", align="L")
    pdf.ln(6)

    pdf.set_font("Helvetica", "", 10.5)
    pdf.set_text_color(71, 85, 105)
    intro_lead = (
        "Have you ever wondered what would happen if you created a tiny planet inside a computer, "
        "scattered grass, trees, and deer on it, gave the little creatures brains to learn from their mistakes, "
        "and then just sat back and watched what happened? That is exactly what this project does. "
        "There are no joystick controls, no game over screens, and no cheat codes -- only real digital life "
        "learning how to survive, grow, and build civilizations."
    )
    pdf.multi_cell(180, 6, intro_lead, align="L")
    pdf.ln(6)

    # Highlights 3-column or 3-box feature cards
    box_w = 56
    box_h = 36
    gap = 6
    start_x = 15
    y_pos = 160

    features = [
        ("The Little Beings", "Animals and people that get hungry, thirsty, sleepy, make friends, and have babies.", (240, 253, 244), (5, 150, 105)),
        ("The Living Brain", "Neural wires that learn: good food feels great, getting bitten hurts, curiosity is fun!", (254, 243, 199), (217, 119, 6)),
        ("The AI God", "Real Google Gemini AI watching from the clouds, answering tribal prayers with miracles.", (239, 246, 255), (37, 99, 246)),
    ]

    for i, (f_title, f_desc, bg, border) in enumerate(features):
        bx = start_x + (i * (box_w + gap))
        pdf.set_fill_color(*bg)
        pdf.set_draw_color(*border)
        pdf.set_line_width(0.6)
        pdf.rect(bx, y_pos, box_w, box_h, style="FD")

        pdf.set_xy(bx + 4, y_pos + 4)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*border)
        pdf.cell(box_w - 8, 5, f_title, align="L")

        pdf.set_xy(bx + 4, y_pos + 12)
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(51, 65, 85)
        pdf.multi_cell(box_w - 8, 4.5, f_desc, align="L")

    # Cover Footer
    pdf.set_xy(15, 240)
    pdf.set_draw_color(226, 232, 240)
    pdf.line(15, 240, 195, 240)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(90, 5, "PROJECT: World Simulator (Artificial Life & Neural Society)", align="L")
    pdf.cell(90, 5, "FORMAT: Plain English Illustrated Guide", align="R")
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.cell(90, 5, "CORE ENGINES: PyGame Sandbox + Neural Brains + Gemini Deity", align="L")
    pdf.cell(90, 5, "AUDIENCE: Kids, Families, Developers & Thinkers", align="R")

    # =========================================================================
    # CHAPTER 1: THE BIG PICTURE
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("1", "The Big Picture: What on Earth is This Project?")

    pdf.body_p(
        "Imagine you have an ant farm on your desk. Inside that ant farm, there is dirt, sugar water, "
        "and hundreds of busy little ants digging tunnels, looking for food, and taking care of their queen. "
        "You do not tell each ant which grain of sand to pick up. You simply watch them figure it out on their own."
    )
    pdf.body_p(
        "Now imagine that ant farm is inside your computer, but instead of just ants, it has an entire living planet! "
        "It has green plains, misty mountains, flowing rivers, apple trees, deer, wolves, and little human beings. "
        "This project is called the World Simulator."
    )

    pdf.section_heading("How is this Different from a Regular Video Game?")
    pdf.body_p(
        "Most computer games are like a stage play where you are the actor. If you play Super Mario and drop your "
        "controller on the floor, Mario stands still forever. Nothing moves until you press a button."
    )
    pdf.body_p(
        "The World Simulator is completely different: it is an AUTONOMOUS SIMULATION. You are not a player; you are "
        "the observer (and sometimes a benevolent deity). If you turn on the simulation and walk away to make lunch, "
        "the digital world keeps living without you: trees grow, deer get thirsty and drink from rivers, rain falls, "
        "humans build campfires, tell stories, and grow old."
    )

    pdf.callout_box(
        "In Simple Words",
        "The Digital Terrarium Rule",
        "In a video game, you control the character. In this World Simulator, every creature has its own tiny mind, "
        "its own feelings, and its own choices. You press 'Play' and watch a miniature history of the universe unfold!",
        "simple"
    )

    pdf.section_heading("Why Did the Creators Build This?")
    pdf.body_p(
        "Scientists, engineers, and curious thinkers have always asked big questions: How did living things start "
        "working together? How did humans discover fire and language? Can artificial intelligence learn just like a puppy "
        "learns by exploring? By building a living miniature digital laboratory, we can watch how nature, intelligence, "
        "and society emerge from simple rules."
    )

    # =========================================================================
    # CHAPTER 2: MEET THE CITIZENS
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("2", "Meet the Citizens: Who Lives in This Digital World?")

    pdf.body_p(
        "Just like our real Earth, the World Simulator has an ecosystem where different creatures depend on "
        "each other. Nobody is useless; every single plant and animal has an important job in keeping nature balanced."
    )

    pdf.section_heading("The Cast of Living Beings")

    pdf.bullet_point("1. Plants & Trees: ", "The Solar-Powered Engines of Life. They don't walk, but they soak up sunlight and turn water into sweet berries, melons, and cucumbers. When eaten, they produce seeds so new trees can sprout.")
    pdf.bullet_point("2. Herbivores (Deer & Rabbits): ", "The Gentle Plant-Lovers. They spend their days wandering through meadows, munching on grass and berries. They are timid and peaceful, but if they hear footsteps or smell danger, they sprint away!")
    pdf.bullet_point("3. Predators (Panthers & Wolves): ", "The Clever Hunters. They are fast, sharp-eyed, and strong. They hunt herbivores to stay alive. Without predators, herbivores would eat every green leaf until the whole planet turned into a desert!")
    pdf.bullet_point("4. Omnivores (Bears & Critters): ", "The Adaptable Foodies. When sweet fruits are ripe, they eat fruit. When winter is harsh and plants freeze, they fish and hunt. They can survive almost anywhere.")
    pdf.bullet_point("5. Humans (Homo Sapiens): ", "The Dreamers & Builders. Humans have the biggest brains in the simulator. They feel cold and build shelters; they make friends and form tribes; they teach their children how to make tools; and they gaze into the stars and pray.")
    pdf.bullet_point("6. The Ancient Monolith: ", "The Mysterious Alien Relic. High in the northern territory stands an ancient black stone. When curious creatures stumble upon it, strange cosmic energy fills their minds with knowledge!")

    pdf.callout_box(
        "Fun Fact",
        "The Balance of Nature",
        "If you remove all the wolves from the world, the deer multiply so fast that they eat all the grass! "
        "Then the deer starve because there is no food left. Predators actually save the ecosystem by keeping "
        "the deer population healthy and balanced.",
        "fun"
    )

    # =========================================================================
    # CHAPTER 3: THE HEARTBEAT & SURVIVAL
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("3", "A Creature's Daily Life: Hunger, Thirst, and Scent Trails")

    pdf.body_p(
        "If you zoom in on any little creature walking across the screen, what is happening inside its body? "
        "Just like you and me, each creature has vital needs that must be satisfied every single minute."
    )

    pdf.section_heading("The Vital Meters (Just like The Sims or a Pet!)")

    pdf.bullet_point("Hunger: ", "Every step burns calories. When the tummy is empty, the creature stops playing and starts searching for food. If hunger hits zero, health starts dropping.")
    pdf.bullet_point("Thirst: ", "Running in the sun makes creatures thirsty. They listen for the sound of rushing water and follow lakes or rivers to take a cool drink.")
    pdf.bullet_point("Energy & Sleep: ", "Creatures get tired! When the sun sets and the stars come out, creatures find a safe tree or cozy cave, curl up, and fall asleep to recharge.")
    pdf.bullet_point("Body Heat: ", "Creatures can freeze during blizzard snowstorms or overheat in desert heatwaves. They seek shade, water, or campfires to stay comfy.")
    pdf.bullet_point("Age & Life Stages: ", "Creatures are born as small babies, grow into energetic young adults, become wise elders, and eventually pass away peacefully of old age.")

    pdf.section_heading("The Secret Superpower: Pheromone Scent Trails")
    pdf.body_p(
        "Have you ever wondered how tiny ants in your garden find a melted ice-cream drop and within 10 minutes there "
        "is a long highway of ants marching towards it? Ants leave invisible scented footprints called Pheromones."
    )
    pdf.body_p(
        "Our World Simulator uses this exact same magic! As creatures explore, they leave invisible scent footprints on the ground:"
    )
    pdf.bullet_point("Green Scent: ", "'Delicious berry bush found over here!' Other hungry animals smell it and follow the trail.")
    pdf.bullet_point("Blue Scent: ", "'Fresh water stream flowing nearby!' Thirsty travelers follow the scent.")
    pdf.bullet_point("Red Scent: ", "'DANGER! A tiger was spotted here!' Creatures smell this warning and run in the opposite direction!")

    pdf.callout_box(
        "Takeaway",
        "Communication Without Words",
        "Creatures don't need cellphones or radios. Through scent trails on the ground, the entire animal kingdom "
        "shares a living GPS map of food, water, and danger!",
        "takeaway"
    )

    # =========================================================================
    # CHAPTER 4: HOW CREATURES THINK
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("4", "The Brain: How Digital Creatures Think (Neural Networks Made Easy)")

    pdf.body_p(
        "People often hear the words 'Artificial Neural Network' and think of frightening, complicated math equations. "
        "Don't worry! In this simulator, a brain works just like a child learning about the world."
    )

    pdf.section_heading("The Lightbulb and Muscle Toy Board")
    pdf.body_p(
        "Imagine a wooden toy board with two rows on it:"
    )
    pdf.bullet_point("Row 1: The Senses (Lightbulbs): ", "These light up whenever the creature experiences something. One bulb lights up if it sees red (a berry). Another lights up if it smells water. Another lights up if it hears a loud growl.")
    pdf.bullet_point("Row 2: The Actions (Muscles): ", "These are buttons that make the body move: 'Walk Forward', 'Turn Around', 'Open Mouth to Eat', or 'Sprint Away'.")
    pdf.bullet_point("The Neural Wires: ", "Tiny wires connect the lightbulbs to the muscles. When a lightbulb turns on, electricity flows through the wire to trigger an action.")

    pdf.section_heading("Learning by Rewards and Regrets")
    pdf.body_p(
        "When a creature is first born, its wires are connected randomly. It doesn't know what an apple is, or what a wolf is! "
        "So it explores:"
    )
    pdf.bullet_point("Trial 1 (The Good Surprise): ", "Baby deer walks towards a red bush and takes a bite. It's a sweet strawberry! Its hunger meter goes up (+20 happiness). The brain immediately thinks: 'YES! That felt amazing!' The wire connecting 'See Red Bush' to 'Eat' becomes twice as thick and strong.")
    pdf.bullet_point("Trial 2 (The Painful Mistake): ", "Baby deer walks towards a spiky cactus and tries to eat it. Ouch! -15 health. The brain thinks: 'NO! That hurt!' The wire connecting 'See Cactus' to 'Eat' gets snipped and weakened.")
    pdf.bullet_point("Result: ", "After just a few minutes of living, the creature naturally runs towards sweet food and avoids spiky dangers -- without any human writing rules for it!")

    pdf.callout_box(
        "In Simple Words",
        "The Secret of Artificial Intelligence",
        "AI is not magic. It is simply a brain that remembers what gave it a reward and what gave it pain. "
        "Over time, good habits become automatic!",
        "simple"
    )

    # =========================================================================
    # CHAPTER 5: MEMORY & WISDOM
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("5", "Memory: Remembering Where the Best Water Springs Are")

    pdf.body_p(
        "A brain without memory is like a goldfish: every second feels like the first second of your life! "
        "To truly survive and build civilizations, creatures need memory. The simulator gives them two distinct kinds:"
    )

    pdf.section_heading("1. Sticky-Note Memory (Short-Term Sensory Buffer)")
    pdf.body_p(
        "This is like a yellow sticky note stuck to the creature's forehead. It holds quick information from the last 10 seconds: "
        "'A wolf growled behind the rock 4 seconds ago!' If the wolf dips behind a tree out of sight, the creature doesn't forget; "
        "it remembers the sticky note and keeps running until it is far away."
    )

    pdf.section_heading("2. The Photo Album (Long-Term Episodic Memory)")
    pdf.body_p(
        "When a creature has an important life event -- finding a sparkling crystal-clear lake, discovering an ancient ruin, "
        "or meeting its life partner -- it stores that memory into a deep, long-term photo album."
    )
    pdf.body_p(
        "Later, if the creature travels 5 miles away into the dry desert and runs out of water, it flips open its mental photo album: "
        "'Aha! Two days ago I drank from the lake near the tall mountains!' It turns around and follows its memory back home."
    )

    pdf.section_heading("3. The Wisdom of Elders: Teaching the Young")
    pdf.body_p(
        "Humans have an extra superpower: they can share memories! When an elder human has survived 50 seasons, "
        "they sit down near the younger tribe members and pass down stories:"
    )
    pdf.bullet_point("Teaching Safe Foods: ", "'Children, the speckled brown mushrooms are poisonous; only pick the bright yellow fruits.'")
    pdf.bullet_point("Teaching Tool Making: ", "'If you bang this hard flint rock against a sturdy stick, you make a sharp spear.'")

    pdf.callout_box(
        "Fun Fact",
        "Cultural Heritage",
        "Because elders pass down memories, a tribe that has lived in the cold snowy mountains for 5 generations "
        "becomes expert shelter builders, while a tribe living in the fertile plains becomes expert farmers!",
        "fun"
    )

    # =========================================================================
    # CHAPTER 6: LIVING NATURE & WEATHER
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("6", "Mother Nature: Soil, Rain, Seasons & Wild Disasters")

    pdf.body_p(
        "The world in our simulator is not a static painted wallpaper. The earth beneath their feet breathes, "
        "the skies change, and nature has its own living rhythm."
    )

    pdf.section_heading("The Circle of Life: How Forests Grow")
    pdf.body_p(
        "Nothing in the world appears out of thin air. Everything follows the laws of nature:"
    )
    pdf.bullet_point("Step 1: The Feast: ", "A deer eats an apple from an old wild apple tree.")
    pdf.bullet_point("Step 2: Dropping Seeds: ", "The deer walks across a barren grassy hill and discards the apple seeds into the soil.")
    pdf.bullet_point("Step 3: The Rain Cloud: ", "A gray storm cloud drifts overhead and pours fresh rain onto the hill. The soil becomes moist and rich.")
    pdf.bullet_point("Step 4: The New Sprout: ", "The seed drinks the water, roots sink into the earth, and a baby sapling bursts through the dirt!")
    pdf.bullet_point("Step 5: A New Forest: ", "Years later, that sapling is a giant tree feeding dozens of new animals. The forest expands naturally across the continent.")

    pdf.section_heading("Dramatic Weather & Wild Disasters")
    pdf.body_p(
        "Life isn't always easy. To test if the creatures are truly smart, the simulator unleashes natural events:"
    )
    pdf.bullet_point("Thunderstorms & Rain: ", "Fills dry riverbeds, quenches plants, and creates cool puddles for animals to drink.")
    pdf.bullet_point("Lightning Strikes & Wildfires: ", "A bolt of lightning can strike dry grass! A fire spreads with the wind, burning down trees and sending animals running. But when the fire burns out, the rich black ash makes the soil ten times more fertile for new flowers!")
    pdf.bullet_point("Summer Droughts & Winter Blizzards: ", "During heatwaves, rivers dry up and food becomes scarce; during blizzards, temperatures plummet and only creatures near warm shelters survive.")

    pdf.callout_box(
        "Takeaway",
        "Survival of the Fittest",
        "Nature's challenges weed out lazy habits. The tribes that plan ahead by storing food, building warm huts, "
        "and helping each other are the ones that survive the bitter winters.",
        "takeaway"
    )

    # =========================================================================
    # CHAPTER 7: FROM CAMPFIRES TO KINGDOMS
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("7", "Civilization: From Campfires to Tribes and Culture")

    pdf.body_p(
        "Solitary animals like panthers live alone. But humans have a special drive built into their code: "
        "the SOCIAL DRIVE. When humans spend time near each other, their happiness goes up and they feel safe."
    )

    pdf.section_heading("Family and Genetics (Inheriting Traits)")
    pdf.body_p(
        "When two creatures fall in love and have a baby, the computer mixes their digital DNA like a deck of cards:"
    )
    pdf.bullet_point("Speed & Stamina: ", "If mom is a fast runner, the baby has a high chance of inheriting long, swift legs.")
    pdf.bullet_point("Curiosity & Brains: ", "If dad loved exploring new hills, the child is born with an adventurous spirit.")
    pdf.bullet_point("Mutations (Surprise Talents!): ", "Every once in a while, a baby is born with a brand-new trait neither parent had -- like thicker fur to resist cold, or a sharper memory!")

    pdf.section_heading("The Birth of Tribes & Technology")
    pdf.body_p(
        "As human families grow, they form Clans and Villages. Together, they achieve things no single human could ever do alone:"
    )
    pdf.bullet_point("Cooperative Hunting: ", "Four hunters surround a large animal, working together to bring back enough meat to feed the whole village for a week.")
    pdf.bullet_point("Tool Inventions (Tech Trees): ", "Humans start with simple clubs, then invent sharp flint daggers, woven fishing baskets, wooden cabins, and durable storage pots.")
    pdf.bullet_point("Village Campfires: ", "At sunset, the clan gathers around a crackling fire. They sing, share food with mothers and babies, and strengthen their clan loyalty.")

    pdf.callout_box(
        "In Simple Words",
        "Why Society Matters",
        "One human alone in the wild is prey for a panther. But ten humans working together with fire and spears "
        "can build a safe village where children can grow up in peace.",
        "simple"
    )

    # =========================================================================
    # CHAPTER 8: THE AI DEITY
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("8", "The AI Deity: When Google's Gemini Watches from the Clouds")

    pdf.body_p(
        "This is one of the most exciting, futuristic features in the entire project! What happens when a human tribe "
        "faces a crisis so terrifying that their own minds cannot solve it?"
    )

    pdf.section_heading("The Leader's Prayer")
    pdf.body_p(
        "Suppose a devastating heatwave has lasted for 30 days. The rivers have dried to dust, the berry bushes are shriveled, "
        "and the village elders have no water left for the children. The clan leader climbs to the highest mountain peak, "
        "kneels before the heavens, and sends out a desperate prayer."
    )

    pdf.section_heading("A Real Artificial Intelligence Listens!")
    pdf.body_p(
        "At that very moment, the simulation reaches out across the Internet to Google's real cloud-based AI: Gemini! "
        "The simulator packages the entire state of the world into a message:"
    )
    pdf.bullet_point("The Message Sent to Gemini: ", "'You are the Divine Deity. Leader Solomon of the SunClan is praying to you. His tribe of 12 people has only 10% water left, and a wildfire approaches from the East. What is your divine guidance?'")
    pdf.bullet_point("Gemini's Living Response: ", "Gemini's deep language model ponders the situation and speaks back in beautiful, solemn words: 'My children of the SunClan, fear not the smoke. Gather your people and travel west towards the ancient stone monolith; beneath its shadow, deep underground springs still bubble with sweet water.'")

    pdf.section_heading("Divine Miracles")
    pdf.body_p(
        "When the tribe demonstrates immense devotion, the Gemini Deity doesn't just speak -- it can trigger divine interventions:"
    )
    pdf.bullet_point("Cosmic Epiphany: ", "A flash of inspiration strikes the tribe, instantly upgrading their knowledge of tool-making and medicine!")
    pdf.bullet_point("The Rain Blessing: ", "Dark storm clouds suddenly gather over the village, quenching the drought and filling the lakes.")
    pdf.bullet_point("The Living Avatar: ", "A glowing deity avatar descends from the sky and walks through the forest, inspiring every creature that sees it!")

    pdf.callout_box(
        "Fun Fact",
        "Real AI in a Simulated Game",
        "Most games have pre-written robot scripts with boring answers like 'Press X to continue'. "
        "In this simulator, Google's real artificial intelligence genuinely reads the world's situation "
        "and invents brand-new, unique prophecies every single time!",
        "fun"
    )

    # =========================================================================
    # CHAPTER 9: UNDER THE HOOD (ENGINE ROOM)
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("9", "Under the Hood: How the Computer Makes It All Run Smoothly")

    pdf.body_p(
        "Now that we know how the creatures live, think, and pray, let's peek under the hood at the engine room. "
        "How can a regular laptop run thousands of trees, creatures, rain clouds, and brains without catching fire?"
    )

    pdf.section_heading("1. The Conductor (The Scheduler)")
    pdf.body_p(
        "Imagine an orchestra with 50 musicians. If the drummer, trumpeter, and violinist all played randomly whenever they "
        "wanted, it would sound like chaotic noise! The orchestra needs a Conductor who waves a baton and keeps the beat."
    )
    pdf.body_p(
        "In our software, this is called the Scheduler. Sixty times every single second (60 ticks per second), the Scheduler waves its baton:"
    )
    pdf.bullet_point("Beat 1: Physics & Movement: ", "Move the legs of every creature and calculate collisions.")
    pdf.bullet_point("Beat 2: Weather & Nature: ", "Drift clouds, spread seeds, and update soil moisture.")
    pdf.bullet_point("Beat 3: Neural Thinking: ", "Let every creature look around, think, and decide its next step.")
    pdf.bullet_point("Beat 4: Draw to Screen: ", "Paint the colorful trees, creatures, and rivers onto your monitor.")

    pdf.section_heading("2. The Super-Fast Desk (Cache Bridge & RAM Buffers)")
    pdf.body_p(
        "If you are doing homework and your textbook is stored in the basement, walking downstairs every 30 seconds to read one page "
        "would make your homework take 10 hours! You keep the textbook right on your desk."
    )
    pdf.body_p(
        "The simulator does this with your computer's RAM memory. It builds pre-allocated fast highways (called Memory Caches). "
        "Creature health, temperatures, and memories are kept right on the desk, so the computer can look up 1,000 creatures in less "
        "than 1 millisecond!"
    )

    pdf.section_heading("3. The Magic Crystal Ball (Save and Load)")
    pdf.body_p(
        "What happens when you need to go to sleep or turn off your computer? You don't want your world to disappear! "
        "The Save System takes an instantaneous snapshot of the entire world -- every tree, seed, drop of water, thought, "
        "and memory -- and packs it safely into a crystal-ball file (.dat file). Tomorrow, you open the file and your world "
        "wakes up in the exact millisecond you left it!"
    )

    pdf.callout_box(
        "Takeaway",
        "Engineering Magic",
        "Good software isn't just about cool features; it's about speed and harmony. "
        "By organizing tasks like an orchestra and keeping data on a super-fast desk, "
        "a whole living world runs smoothly at 60 frames per second!",
        "takeaway"
    )

    # =========================================================================
    # CHAPTER 10: THE GOD MODE DASHBOARD
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("10", "The God Mode Dashboard: How You Watch and Explore")

    pdf.body_p(
        "When you launch the project by running 'py run_gui.py', a colorful window opens on your screen. "
        "This is your God Mode Dashboard. Let's see what you can do!"
    )

    pdf.section_heading("1. The Living Interactive Map")
    pdf.body_p(
        "You can zoom in and out with your mouse wheel, or pan across mountains and oceans. "
        "You'll see green forests, shimmering blue rivers, tiny brown deer darting through grass, "
        "and little humans carrying torches near their village campfire."
    )

    pdf.section_heading("2. The Mind-Reader Inspector Tool")
    pdf.body_p(
        "Click your mouse on ANY creature on screen! A transparent window opens up showing everything inside that creature's mind:"
    )
    pdf.bullet_point("Identity: ", "Name: 'Aria', Species: Homo Sapiens, Age: 24, Clan: 'RiverWalkers'")
    pdf.bullet_point("Vitals: ", "Health: 94%, Hunger: 35%, Thirst: 12% (Thirsty!), Energy: 80%")
    pdf.bullet_point("Current Thought: ", "'Walking towards the blue river scent trail to drink fresh water.'")
    pdf.bullet_point("Memories: ", "Recent memories of meeting friend 'Leo' and finding a blackberry bush yesterday.")

    pdf.section_heading("3. Heatmap X-Ray Vision")
    pdf.body_p(
        "Want to see invisible forces? Press a key to toggle Heatmap views:"
    )
    pdf.bullet_point("Thermal Heatmap: ", "Cold mountains glow icy blue; hot deserts and campfires glow fiery orange.")
    pdf.bullet_point("Food Density: ", "Lush fruit groves glow bright emerald green; barren deserts turn gray.")
    pdf.bullet_point("Pheromone Trails: ", "Watch the invisible scented highways of the animal kingdom light up like glowing neon paths!")

    pdf.section_heading("4. The God Mode Sandbox Controls")
    pdf.body_p(
        "You can just sit back and watch, or you can intervene:"
    )
    pdf.bullet_point("Drop Rations: ", "Feeling generous? Click a button to shower 20 apples into a starving village.")
    pdf.bullet_point("Summon Storms: ", "Click to summon thunderclouds over dry farmland.")
    pdf.bullet_point("Test the Clan: ", "Spawn a wolf pack nearby to see if the village guards use their spears to defend the camp!")

    pdf.callout_box(
        "In Simple Words",
        "Your Window into Another Universe",
        "The dashboard turns your computer screen into a window looking down at an alien planet. "
        "You have front-row seats to the drama, triumphs, and adventures of digital evolution!",
        "simple"
    )

    # =========================================================================
    # CHAPTER 11: SUMMARY & CHEAT SHEET
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("11", "The Cheat Sheet: Everything You Need to Know at a Glance")

    pdf.body_p(
        "Here is a quick, handy summary table comparing real life to how our World Simulator brings it to life inside code:"
    )

    # Summary Table
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(30, 58, 138)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(50, 7, "REAL WORLD THING", border=1, fill=True, align="C")
    pdf.cell(55, 7, "SIMULATOR SYSTEM", border=1, fill=True, align="C")
    pdf.cell(75, 7, "IN SIMPLE WORDS", border=1, fill=True, align="C")
    pdf.ln(7)

    table_data = [
        ("Animal Brain", "Neural Network (Brain.py)", "Wires that get stronger when things feel good, weaker when they hurt."),
        ("Scent Trails", "PheromoneGrid", "Invisible smelly footprints that guide others to water and food."),
        ("Memories & Diaries", "CognitiveMemory", "Sticky notes for short term; photo albums for remembering old watering holes."),
        ("Forests & Plants", "Soil & Seed Systems", "Fruits eaten -> seeds dropped -> rain falls -> new trees sprout!"),
        ("Weather & Seasons", "WeatherManager", "Wind pushes clouds, clouds drop rain, winter freezes lakes."),
        ("Villages & Tribes", "CivilizationSystem", "Humans gather by campfires, share food, and teach children how to make tools."),
        ("Prayers & Miracles", "Gemini AI Deity", "Real Google AI listens to tribal leaders and sends prophecies and rain."),
        ("Saving Your Game", "SaveSystem (.dat files)", "Freezes the entire planet in a crystal jar so you can resume tomorrow."),
        ("Orchestra Conductor", "Scheduler.py", "Keeps all systems moving in perfect harmony 60 times a second."),
    ]

    pdf.set_font("Helvetica", "", 8.5)
    for i, (col1, col2, col3) in enumerate(table_data):
        if i % 2 == 0:
            pdf.set_fill_color(248, 250, 252)  # very light gray
        else:
            pdf.set_fill_color(255, 255, 255)  # white

        pdf.set_text_color(30, 41, 59)
        pdf.cell(50, 6.5, col1, border=1, fill=True, align="L")
        pdf.cell(55, 6.5, col2, border=1, fill=True, align="L")
        pdf.cell(75, 6.5, col3, border=1, fill=True, align="L")
        pdf.ln(6.5)

    pdf.ln(6)
    pdf.section_heading("Three Frequently Asked Questions")

    pdf.bullet_point("Q: Can all the creatures die out completely? ", "A: Yes! If a severe drought lasts too long and the creatures haven't learned to store food or find water, extinction can happen. That is what makes their survival so impressive when they succeed!")
    pdf.bullet_point("Q: Do the creatures have real feelings? ", "A: They have digital drives. When their hunger bar is low, their code sends a signal of 'Distress' and they frantically seek food. When well-fed and near friends, their code sends 'Contentment' and they play!")
    pdf.bullet_point("Q: How do I run the project? ", "A: Open your terminal, go to the folder, and type: py run_gui.py. The window opens up and your world comes alive immediately!")

    pdf.ln(4)
    pdf.callout_box(
        "Final Thought",
        "The Miracle of Emergence",
        "The most magical lesson of this project is called 'Emergence'. None of the individual rules are complicated: "
        "eat food, drink water, stay warm, seek friends. But when you put hundreds of simple creatures together, "
        "something breathtaking happens: tribes form, cultures appear, trails are blazed, and a living, breathing history "
        "comes alive right in front of your eyes.",
        "takeaway"
    )

    # Save output
    pdf.output(output_path)
    print(f"Successfully generated PDF guide at: {output_path}")


if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    target_pdf = os.path.join(out_dir, "World_Simulator_Explained_Simple_Guide.pdf")
    generate_guide_pdf(target_pdf)
