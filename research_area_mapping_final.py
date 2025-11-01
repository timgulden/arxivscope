# RAND Research Area Mapping - Final Version
# Maps local_data values to research areas based on RAND's actual organizational structure
# Includes historical divisions and improved categorization

RESEARCH_AREA_MAPPING = {
    # RAND Army Research Division (Arroyo Center) - Army FFRDC
    'Arroyo Center': 'RAND Army Research Division',
    'Arroyo Center.': 'RAND Army Research Division',
    'Arroyo center': 'RAND Army Research Division',
    'RAND Army Research Division': 'RAND Army Research Division',
    'Army Research Division': 'RAND Army Research Division',
    'Army Research': 'RAND Army Research Division',
    
    # Forces and Logistics Program (Arroyo)
    'Forces and Logistics': 'RAND Army Research Division',
    'Forces and Logistics Program': 'RAND Army Research Division',
    'Logistics': 'RAND Army Research Division',
    'Logistics.': 'RAND Army Research Division',
    'Losgistics': 'RAND Army Research Division',
    'Logistic': 'RAND Army Research Division',
    'Logistics Systems Laboratory': 'RAND Army Research Division',
    
    # Personnel, Training, and Health Program (Arroyo)
    'Personnel Training and Health': 'RAND Army Research Division',
    'Personnel, Training, and Health': 'RAND Army Research Division',
    'Personnel, Training, and Health Program': 'RAND Army Research Division',
    'Personnel Training and Health Program': 'RAND Army Research Division',
    'Personnel': 'RAND Army Research Division',
    'Manpower Personnel and Training Program': 'RAND Army Research Division',
    'Manpower, Personnel, and Training Program': 'RAND Army Research Division',
    'Manpower, Personnel, and Training': 'RAND Army Research Division',
    
    # Strategy, Doctrine, and Resources Program (Arroyo)
    'Strategy and Resources Program': 'RAND Army Research Division',
    'Strategy, Doctrine, and Resources Program': 'RAND Army Research Division',
    'Strategy, Doctrine, and Resources': 'RAND Army Research Division',
    'Strategy Policy and Operations Program': 'RAND Army Research Division',
    'Strategy Policy  and Operations Program': 'RAND Army Research Division',
    'Strategy, Policy, and Operations Program': 'RAND Army Research Division',
    
    # Historical Army divisions
    'Tactical Operations': 'RAND Army Research Division',
    'Plans Analysis': 'RAND Army Research Division',
    'Preliminary Design Section': 'RAND Army Research Division',
    'Military Operations Simulation Facility': 'RAND Army Research Division',
    'Washington Defense Research Division': 'RAND Army Research Division',
    'Washington Research': 'RAND Army Research Division',
    'Washington Office': 'RAND Army Research Division',
    
    # RAND Project AIR FORCE - Air Force FFRDC
    'Project Air Force': 'RAND Project AIR FORCE',
    'Project Air Force.': 'RAND Project AIR FORCE',
    'Project AIR FORCE': 'RAND Project AIR FORCE',
    'RAND Project AIR FORCE': 'RAND Project AIR FORCE',
    'RAND Project Air Force': 'RAND Project AIR FORCE',
    'RAND Project AIR FORCE Division': 'RAND Project AIR FORCE',
    
    # Force Modernization and Employment Program (PAF)
    'Force Modernization and Employment Program': 'RAND Project AIR FORCE',
    'Force Employment Program': 'RAND Project AIR FORCE',
    'Force Structure and Modernization': 'RAND Project AIR FORCE',
    
    # Resource Management Program (PAF)
    'Resource Management Program': 'RAND Project AIR FORCE',
    'Resource Analysis': 'RAND Project AIR FORCE',
    'Resource analysis': 'RAND Project AIR FORCE',
    'Resource Management': 'RAND Project AIR FORCE',
    'Resource Management and System Acquisition': 'RAND Project AIR FORCE',
    'Resource Management and System Acquisition.': 'RAND Project AIR FORCE',
    'Resource Management, Human Capital': 'RAND Project AIR FORCE',
    
    # Strategy and Doctrine Program (PAF) - Note: This could be Arroyo or PAF
    'Strategy and Doctrine Program': 'RAND Project AIR FORCE',
    'Strategy and Doctrine (Air Force)': 'RAND Project AIR FORCE',
    
    # Workforce, Development, and Health Program (PAF)
    'Workforce, Development, and Health Program': 'RAND Project AIR FORCE',
    
    # Air Force specific technical areas
    'Aero-Astronautics': 'RAND Project AIR FORCE',
    'Aero-astronautics': 'RAND Project AIR FORCE',
    'Aero Astronautics': 'RAND Project AIR FORCE',
    'Aircraft': 'RAND Project AIR FORCE',
    'Missiles': 'RAND Project AIR FORCE',
    'Missiles.': 'RAND Project AIR FORCE',
    'Airborne Vehicles': 'RAND Project AIR FORCE',
    'Bomber Group': 'RAND Project AIR FORCE',
    'Propulsion Group': 'RAND Project AIR FORCE',
    
    # RAND National Security Research Division - Navy/Marine FFRDC
    'RAND National Security Research Division': 'RAND National Security Research Division',
    'National Security Research Division': 'RAND National Security Research Division',
    'National Security Research Division.': 'RAND National Security Research Division',
    'National Security Research': 'RAND National Security Research Division',
    'National Security Research Diviision': 'RAND National Security Research Division',
    
    # Acquisition and Technology Policy Program (NSRD)
    'Acquisition and Technology Policy Center': 'RAND National Security Research Division',
    'Acquisition and Technology Policy Program': 'RAND National Security Research Division',
    'Acquisition and Development Program': 'RAND National Security Research Division',
    'Acquisitions and Development Program': 'RAND National Security Research Division',
    'Acquisition and Support Policy': 'RAND National Security Research Division',
    'Acquisition': 'RAND National Security Research Division',
    
    # Personnel, Readiness, and Health Program (NSRD)
    'Personnel, Readiness, and Health Program': 'RAND National Security Research Division',
    'Defense Manpower Research Center': 'RAND National Security Research Division',
    'Defense Manpower Research': 'RAND National Security Research Division',
    
    # International Security and Defense Policy Program (NSRD)
    'International Security and Defense Policy Center': 'RAND National Security Research Division',
    'International Security and Defense Policy': 'RAND National Security Research Division',
    'International Security and Defense Strategy': 'RAND National Security Research Division',
    'international security and defense strategy': 'RAND National Security Research Division',
    'Defense Planning and Analysis': 'RAND National Security Research Division',
    'Defense and Technology Planning': 'RAND National Security Research Division',
    'Defense Policy Analysis': 'RAND National Security Research Division',
    'Defense Policy and Analysis': 'RAND National Security Research Division',
    'Forces and Resources Policy Center': 'RAND National Security Research Division',
    'Defense Advisory Group': 'RAND National Security Research Division',
    'Defense Technologies and Planning': 'RAND National Security Research Division',
    'Defense Technology and Planning': 'RAND National Security Research Division',
    'Strategic Communications': 'RAND National Security Research Division',
    'National Security Strategies': 'RAND National Security Research Division',
    'National Security Strategies Program': 'RAND National Security Research Division',
    'National Security Study Directive (NSSD)': 'RAND National Security Research Division',
    'National Security Defense Division': 'RAND National Security Research Division',
    'National Security Research Institute': 'RAND National Security Research Division',
    'RAND National Security Research Institute': 'RAND National Security Research Division',
    'RAND Security Defense Research Division': 'RAND National Security Research Division',
    'Nattional Defense Research Institute': 'RAND National Security Research Division',
    
    # Navy and Marine Forces Program (NSRD)
    'Navy and Marine Forces Center': 'RAND National Security Research Division',
    'National Defense Research Institute': 'RAND National Security Research Division',
    'National Defense Research Division': 'RAND National Security Research Division',
    
    # RAND Homeland Security Research Division - DHS FFRDC
    'RAND Homeland Security Research Division': 'RAND Homeland Security Research Division',
    'Homeland Security Research Division': 'RAND Homeland Security Research Division',
    'Homeland Security Operational Analysis Center': 'RAND Homeland Security Research Division',
    
    # Management, Technology and Capabilities Program (HSRD)
    'Management, Technology and Capabilities Program': 'RAND Homeland Security Research Division',
    'Management Sciences': 'RAND Homeland Security Research Division',
    'Managements Sciences': 'RAND Homeland Security Research Division',
    'Management Sciences Engineering Sciences': 'RAND Homeland Security Research Division',
    
    # Disaster Management and Resilience Program (HSRD)
    'Disaster Management and Resilience Program': 'RAND Homeland Security Research Division',
    
    # Infrastructure, Immigration & Security Operations Program (HSRD)
    'Infrastructure, Immigration & Security Operations Program': 'RAND Homeland Security Research Division',
    'Infrastructure, Safety, and Environment': 'RAND Homeland Security Research Division',
    'infrastructure, Safety, and Environment': 'RAND Homeland Security Research Division',
    'Infrastructure, Safety and Environment': 'RAND Homeland Security Research Division',
    'Infrastructure, Safety & Environment': 'RAND Homeland Security Research Division',
    'Infrastructure Resilience and Environmental Policy': 'RAND Homeland Security Research Division',
    'Rand Infrastructure, Safety, and Environment': 'RAND Homeland Security Research Division',
    'Rand Infrastructure, Safety, and Environment (Organization)': 'RAND Homeland Security Research Division',
    
    # RAND Health - Health policy research
    'RAND Health': 'RAND Health',
    'RAND Health Care': 'RAND Health',
    'Health Care': 'RAND Health',
    'Rand Health': 'RAND Health',
    'Health Sciences': 'RAND Health',
    'Health Promotion and Disease Prevention': 'RAND Health',
    'Population Health': 'RAND Health',
    'Global Health': 'RAND Health',
    'Health Services Delivery Systems': 'RAND Health',
    'Center for Military Health Policy Research': 'RAND Health',
    'Center for the Study of Employee Health Benefits': 'RAND Health',
    'Center for Domestic and International Health Security': 'RAND Health',
    'Health Sciences Program': 'RAND Health',
    'Community Health and Environmental Policy': 'RAND Health',
    'RAND/UCLA Center for Health Policy Study': 'RAND Health',
    
    # Access and Delivery Program (Health)
    'Access and Delivery Program': 'RAND Health',
    
    # Payment, Cost, and Coverage Program (Health)
    'Payment, Cost, and Coverage Program': 'RAND Health',
    'Cost Analysis': 'RAND Health',
    'Cost analysis': 'RAND Health',
    'COST ANALYSIS': 'RAND Health',
    
    # Quality Measurement and Improvement Program (Health)
    'Quality Measurement and Improvement Program': 'RAND Health',
    
    # Historical health divisions
    'Drug Policy Research Center': 'RAND Health',
    'RAND Drug Policy Research Center': 'RAND Health',
    
    # RAND Education, Employment, and Infrastructure - Education and workforce
    'RAND Education, Employment, and Infrastructure': 'RAND Education, Employment, and Infrastructure',
    'RAND Education and Labor': 'RAND Education, Employment, and Infrastructure',
    'RAND Education': 'RAND Education, Employment, and Infrastructure',
    'Rand Education': 'RAND Education, Employment, and Infrastructure',
    'Rand Education.': 'RAND Education, Employment, and Infrastructure',
    'Education and Labor': 'RAND Education, Employment, and Infrastructure',
    
    # Labor and Workforce Development Program (EEI)
    'Labor and Workforce Development Program': 'RAND Education, Employment, and Infrastructure',
    'Labor and Population Program': 'RAND Education, Employment, and Infrastructure',
    'Labor and Population Program.': 'RAND Education, Employment, and Infrastructure',
    'Labor and Population': 'RAND Education, Employment, and Infrastructure',
    'Labor & Population': 'RAND Education, Employment, and Infrastructure',
    
    # PreK–12 Educational Systems Program (EEI)
    'PreK–12 Educational Systems Program': 'RAND Education, Employment, and Infrastructure',
    'PreK-12 Instructional Improvement': 'RAND Education, Employment, and Infrastructure',
    
    # Legacy Justice, Infrastructure & Environment (now part of EEI and HSRD)
    'RAND Justice, Infrastructure, and Environment': 'RAND Education, Employment, and Infrastructure',
    'Justice, Infrastructure, and Environment': 'RAND Education, Employment, and Infrastructure',
    'Justice, Infrastructure and Environment': 'RAND Education, Employment, and Infrastructure',
    'Justice and Environment': 'RAND Education, Employment, and Infrastructure',
    'Environmental Sciences': 'RAND Education, Employment, and Infrastructure',
    'Justice Policy': 'RAND Education, Employment, and Infrastructure',
    'Criminal Justice': 'RAND Education, Employment, and Infrastructure',
    'Criminal Justice Program': 'RAND Education, Employment, and Infrastructure',
    'Public Safety and Justice Program': 'RAND Education, Employment, and Infrastructure',
    'Public Safety and Justice': 'RAND Education, Employment, and Infrastructure',
    'Institute for Civil Justice': 'RAND Education, Employment, and Infrastructure',
    'Institute for Civil Justice (U.S.)': 'RAND Education, Employment, and Infrastructure',
    'Rand Infrastructure, Safety, and Environment': 'RAND Education, Employment, and Infrastructure',
    'RAND Law, Business, and Regulation': 'RAND Education, Employment, and Infrastructure',
    'RAND Law, Business, and Regulation.': 'RAND Education, Employment, and Infrastructure',
    'Law, Business, and Regulation': 'RAND Education, Employment, and Infrastructure',
    'Rand Justice, Infrastructure, and Environment': 'RAND Education, Employment, and Infrastructure',
    'RAND, Justice, Infrastructure, and Environment': 'RAND Education, Employment, and Infrastructure',
    
    # RAND Europe - International research
    'RAND Europe': 'RAND Europe',
    'Rand Europe': 'RAND Europe',
    'RAND Europe.': 'RAND Europe',
    
    # Defence, Security and Justice (RAND Europe)
    'Defence, Security and Justice': 'RAND Europe',
    
    # Education, Employment and Skills (RAND Europe)
    'Education, Employment and Skills': 'RAND Europe',
    
    # Health and Care (RAND Europe)
    'Health and Care': 'RAND Europe',
    
    # Science and Emerging Technology (RAND Europe)
    'Science and Emerging Technology': 'RAND Europe',
    
    # RAND Australia - Asia-Pacific research
    'RAND Australia': 'RAND Australia',
    
    # RAND Global and Emerging Risks - Global security and emerging threats
    'RAND Global and Emerging Risks': 'RAND Global and Emerging Risks',
    'RAND Global & Emerging Risks': 'RAND Global and Emerging Risks',
    'RAND International': 'RAND Global and Emerging Risks',
    'RAND International Programs': 'RAND Global and Emerging Risks',
    'International Programs': 'RAND Global and Emerging Risks',
    'International': 'RAND Global and Emerging Risks',
    'International Policy': 'RAND Global and Emerging Risks',
    'International Economic Policy': 'RAND Global and Emerging Risks',
    'New York City RAND Institute': 'RAND Global and Emerging Risks',
    'Rand-Qatar Policy Institute': 'RAND Global and Emerging Risks',
    'RAND-Qatar Policy Institute': 'RAND Global and Emerging Risks',
    'RAND Gulf States Policy Institute': 'RAND Global and Emerging Risks',
    'Gulf States Policy Institute': 'RAND Global and Emerging Risks',
    'Rand Gulf States Policy Institute': 'RAND Global and Emerging Risks',
    'Center for Asia-Pacific Policy': 'RAND Global and Emerging Risks',
    'Center for Asia Pacific Policy': 'RAND Global and Emerging Risks',
    'RAND Center for Asia Pacific Policy': 'RAND Global and Emerging Risks',
    'Center for Russian and Eurasian Studies': 'RAND Global and Emerging Risks',
    'Center for Russia and Eurasia': 'RAND Global and Emerging Risks',
    'Center for Global Risk and Security': 'RAND Global and Emerging Risks',
    'Center for Middle East Public Policy': 'RAND Global and Emerging Risks',
    'Center for Middle East Policy': 'RAND Global and Emerging Risks',
    'Center for Terrorism Risk Management Policy': 'RAND Global and Emerging Risks',
    'RAND Center for Terrorism Risk Management Policy': 'RAND Global and Emerging Risks',
    'European-American Center for Policy Analysis': 'RAND Global and Emerging Risks',
    
    # RAND School of Public Policy - Graduate education (Pardee RAND)
    'RAND School of Public Policy': 'RAND School of Public Policy',
    'Pardee RAND Graduate School': 'RAND School of Public Policy',
    'Pardee RAND': 'RAND School of Public Policy',
    'Pardee Rand Graduate School': 'RAND School of Public Policy',
    'Rand Graduate School': 'RAND School of Public Policy',
    'RAND Graduate School': 'RAND School of Public Policy',
    'RAND Graduate Institute': 'RAND School of Public Policy',
    'Rand Graduate Institute': 'RAND School of Public Policy',
    'Rand Institute on Education & Training': 'RAND School of Public Policy',
    'RAND Pardee Center': 'RAND School of Public Policy',
    'RAND Pardee Center.': 'RAND School of Public Policy',
    'PARDEE RAND': 'RAND School of Public Policy',
    'RAND Frederick S. Pardee Center for Longer Range Global Policy and the Future Human Condition': 'RAND School of Public Policy',
    
    # Global Research Talent - Cross-cutting research departments
    'Global Research Talent': 'Global Research Talent',
    
    # Behavioral and Policy Sciences Department (GRT)
    'Behavioral Sciences': 'Global Research Talent',
    'Behavioral and Policy Sciences Department': 'Global Research Talent',
    
    # Defense and Political Sciences Department (GRT)
    'Defense and Political Sciences Department': 'Global Research Talent',
    'Political Science': 'Global Research Talent',
    'Political Science.': 'Global Research Talent',
    'Political science': 'Global Research Talent',
    
    # Economics, Sociology, and Statistics Department (GRT)
    'Economics, Sociology, and Statistics Department': 'Global Research Talent',
    'Economics': 'Global Research Talent',
    'Economics.': 'Global Research Talent',
    'Social Sciences': 'Global Research Talent',
    'Social sciences': 'Global Research Talent',
    'Social Science': 'Global Research Talent',
    'Social Policy': 'Global Research Talent',
    'Social and Behavioral Policy': 'Global Research Talent',
    'RAND Social and Economic Well-Being': 'Global Research Talent',
    'RAND Social and Economic Wellbeing': 'Global Research Talent',
    'Social and Economic Well-Being': 'Global Research Talent',
    'Social and Economic Wellbeing': 'Global Research Talent',
    'Social and Economic Well Being': 'Global Research Talent',
    
    # Engineering and Applied Sciences Department (GRT)
    'Engineering and Applied Sciences Department': 'Global Research Talent',
    'Engineering': 'Global Research Talent',
    'Engineering Sciences': 'Global Research Talent',
    'Engineering and Applied Sciences': 'Global Research Talent',
    'Engineering Analysis': 'Global Research Talent',
    'Engineering and Social Science': 'Global Research Talent',
    'Computer Sciences': 'Global Research Talent',
    'Computer Science': 'Global Research Talent',
    'Computer sciences': 'Global Research Talent',
    'computer science': 'Global Research Talent',
    'Computer Science-Mathematics': 'Global Research Talent',
    'Computer Information Systems': 'Global Research Talent',
    'Computer Analysis': 'Global Research Talent',
    'Information Sciences': 'Global Research Talent',
    'Information Science Methodologies': 'Global Research Talent',
    'Information Processing Systems': 'Global Research Talent',
    'Business Information Systems': 'Global Research Talent',
    'Center for Information-Revolution Analysis': 'Global Research Talent',
    'Mathematics': 'Global Research Talent',
    'Mathematics-Red Wood': 'Global Research Talent',
    'Mathematic sematics': 'Global Research Talent',
    'Numerical Analysis': 'Global Research Talent',
    'Numerican Analysis': 'Global Research Talent',
    'Physics': 'Global Research Talent',
    'Physical Sciences': 'Global Research Talent',
    'Nuclear Sciences': 'Global Research Talent',
    'Nuclear Energy': 'Global Research Talent',
    'Electronics': 'Global Research Talent',
    'Electronic': 'Global Research Talent',
    'Geophysics and Astronomy': 'Global Research Talent',
    'Planetary Sciences': 'Global Research Talent',
    'Planetary Science': 'Global Research Talent',
    'Systems Sciences': 'Global Research Talent',
    'Systems Operations': 'Global Research Talent',
    'Systems operations': 'Global Research Talent',
    'Systems Operations - Red Wood': 'Global Research Talent',
    'Mathematics and Systems Operations': 'Global Research Talent',
    'Systems Development Division': 'Global Research Talent',
    'Systems Development Division.': 'Global Research Talent',
    'Science and Technology Policy Institute': 'Global Research Talent',
    'Science and technology Division': 'Global Research Talent',
    'RAND Science and Technology': 'Global Research Talent',
    'Applied Science and Technology': 'Global Research Talent',
    'Applied Sciences': 'Global Research Talent',
    'Critical Technologies Institute': 'Global Research Talent',
    'Aerospace and Strategic Technology': 'Global Research Talent',
    'Mechanical Sciences': 'Global Research Talent',
    'Plant Science': 'Global Research Talent',
    'Respiration': 'Global Research Talent',
    'Cognitive Science': 'Global Research Talent',
    'Linguistics': 'Global Research Talent',
    'Business management': 'Global Research Talent',
    'Communications': 'Global Research Talent',
    'Intelligence Policy Center': 'Global Research Talent',
    'Cyber and Intelligence Policy Center': 'Global Research Talent',
    'Survey Research Group': 'Global Research Talent',
    
    # Research Residents and Specialists Department (GRT)
    'Research Residents and Specialists Department': 'Global Research Talent',
    
    # Corporate & Administration - General RAND Corporation operations
    'RAND Corporation': 'Corporate & Administration',
    'Rand Corporation': 'Corporate & Administration',
    'Rand Corporation.': 'Corporate & Administration',
    'Rand Corporaton': 'Corporate & Administration',
    'Rand Corportaion': 'Corporate & Administration',
    'Rand corporation': 'Corporate & Administration',
    'RAND': 'Corporate & Administration',
    'Administration': 'Corporate & Administration',
    'Administration.': 'Corporate & Administration',
    'Office of External Affairs': 'Corporate & Administration',
    'RAND Office of External Affairs': 'Corporate & Administration',
    'RAND Office of External Affairs.': 'Corporate & Administration',
    'Office of Services': 'Corporate & Administration',
    'Office of Congressional Relations': 'Corporate & Administration',
    'Office of The President': 'Corporate & Administration',
    'President Office': 'Corporate & Administration',
    'VPFA': 'Corporate & Administration',
    'Mail and Records': 'Corporate & Administration',
    'Research Staff Management Department': 'Corporate & Administration',
    'RAND Institutional': 'Corporate & Administration',
    'RAND Institutional - General': 'Corporate & Administration',
    'RAND Corporate': 'Corporate & Administration',
    'RAND Internal Research and Development': 'Corporate & Administration',
    'RAND-Sponsored Research': 'Corporate & Administration',
    'RAND Enterprise Analysis': 'Corporate & Administration',
    'Research Council': 'Corporate & Administration',
    'Research Programming': 'Corporate & Administration',
    'Publications': 'Corporate & Administration',
    'Reports': 'Corporate & Administration',
    'Library': 'Corporate & Administration',
    'Sub-Contractor': 'Corporate & Administration',
    'Sub-Contractors': 'Corporate & Administration',
    'Project Rand (United States. Air Force)': 'Corporate & Administration',
    'PRO': 'Corporate & Administration',
    'Project RAND': 'Corporate & Administration',
    'Rad': 'Corporate & Administration',
    'RD': 'Corporate & Administration',
    'NA': 'Corporate & Administration',
    'FISC': 'Corporate & Administration',
    'ISA': 'Corporate & Administration',
    'FO': 'Corporate & Administration',
    'CCOM': 'Corporate & Administration',
    'SD': 'Corporate & Administration',
    'STP': 'Corporate & Administration',
    'C3I': 'Corporate & Administration',
    'MIS': 'Corporate & Administration',
    'LSL': 'Corporate & Administration',
    'TechCo': 'Corporate & Administration',
    'TIS Staff': 'Corporate & Administration',
    'SRL Staff and Systems Training Project Staff': 'Corporate & Administration',
    
    # Legacy and historical categories
    'Domestic Research': 'Corporate & Administration',
    'Domestic research': 'Corporate & Administration',
    'Domestic Programs Division': 'Corporate & Administration',
    'Domestic Programs': 'Corporate & Administration',
    'Investment in People and Ideas': 'Corporate & Administration',
    'Human Capital': 'Corporate & Administration',
    'Human and Material Resource Policy': 'Corporate & Administration',
    'Human and Material Resources Policy': 'Corporate & Administration',
    'Human and Material Research Policy': 'Corporate & Administration',
    
    # Empty or null values
    '': 'Uncategorized',
    None: 'Uncategorized',
}

def get_research_area_mapping():
    """Get the research area mapping dictionary."""
    return RESEARCH_AREA_MAPPING

def get_research_areas():
    """Get list of unique research areas."""
    return sorted(set(RESEARCH_AREA_MAPPING.values()))

def categorize_local_data(local_data_value):
    """Categorize a local_data value into a research area."""
    if local_data_value is None or local_data_value.strip() == '':
        return 'Uncategorized'
    return RESEARCH_AREA_MAPPING.get(local_data_value, 'Uncategorized')

if __name__ == "__main__":
    print('Final RAND Research Area Mapping Analysis')
    print(f'Total mappings: {len(RESEARCH_AREA_MAPPING)}')
    print()
    print('Categories (based on current organizational structure):')
    categories = get_research_areas()
    for i, cat in enumerate(categories, 1):
        count = sum(1 for v in RESEARCH_AREA_MAPPING.values() if v == cat)
        print(f'{i:2d}. {cat} ({count} divisions)')

