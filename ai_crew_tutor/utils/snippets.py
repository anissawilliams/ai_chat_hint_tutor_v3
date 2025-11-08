"""
Code snippets database organized by persona
"""

CODE_SNIPPETS = {
    'Nova': {
        'name': "Nova's Cosmic Collection",
        'icon': '🌟',
        'snippets': [
            {
                'title': 'Stream Filter & Map',
                'description': 'Transform data like constellations',
                'code': '''List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5);
List<Integer> doubled = numbers.stream()
    .filter(n -> n % 2 == 0)
    .map(n -> n * 2)
    .collect(Collectors.toList());''',
                'tier': 0
            },
            {
                'title': 'Lambda Function',
                'description': 'Elegant functional orbit',
                'code': '''Function<String, Integer> length = s -> s.length();
int result = length.apply("Nova");''',
                'tier': 0
            },
            {
                'title': 'Optional Handling',
                'description': 'Navigate the void safely',
                'code': '''Optional<String> name = Optional.ofNullable(getUserName());
String result = name.orElse("Unknown Traveler");''',
                'tier': 25
            },
            {
                'title': 'Stream Reduce',
                'description': 'Collapse the universe into one',
                'code': '''int sum = numbers.stream()
    .reduce(0, (a, b) -> a + b);''',
                'tier': 25
            },
            {
                'title': 'Collectors groupingBy',
                'description': 'Organize galaxies by type',
                'code': '''Map<String, List<Person>> grouped = people.stream()
    .collect(Collectors.groupingBy(Person::getType));''',
                'tier': 50
            },
            {
                'title': 'Parallel Streams',
                'description': 'Process multiple star systems',
                'code': '''long count = data.parallelStream()
    .filter(d -> d.getValue() > threshold)
    .count();''',
                'tier': 50
            }
        ]
    },
    'Batman': {
        'name': "Batman's Arsenal",
        'icon': '🦇',
        'snippets': [
            {
                'title': 'Try-Catch Pattern',
                'description': 'Catch criminals (exceptions)',
                'code': '''try {
    riskyOperation();
} catch (SpecificException e) {
    logger.error("Threat detected: " + e.getMessage());
    handleThreat(e);
} finally {
    cleanup();
}''',
                'tier': 0
            },
            {
                'title': 'Debug Logger',
                'description': 'Track evidence',
                'code': '''private static final Logger log = LoggerFactory.getLogger(Detective.class);

public void investigate() {
    log.debug("Starting investigation...");
    log.info("Clue found: {}", evidence);
    log.error("Threat level: CRITICAL");
}''',
                'tier': 0
            },
            {
                'title': 'Null Check Guard',
                'description': 'Defensive programming',
                'code': '''public void process(Object data) {
    if (data == null) {
        throw new IllegalArgumentException("Target cannot be null");
    }
    // Safe to proceed
}''',
                'tier': 25
            },
            {
                'title': 'Custom Exception',
                'description': 'Classify threats',
                'code': '''public class ThreatException extends Exception {
    private final ThreatLevel level;
    
    public ThreatException(String message, ThreatLevel level) {
        super(message);
        this.level = level;
    }
}''',
                'tier': 50
            }
        ]
    },
    'Spider-Gwen': {
        'name': "Spider-Gwen's Web",
        'icon': '🕷️',
        'snippets': [
            {
                'title': 'Thread Creation',
                'description': 'Swing through parallel tasks',
                'code': '''Thread webSwing = new Thread(() -> {
    System.out.println("Swinging through the city!");
});
webSwing.start();''',
                'tier': 0
            },
            {
                'title': 'ExecutorService',
                'description': 'Coordinate multiple swings',
                'code': '''ExecutorService executor = Executors.newFixedThreadPool(4);
executor.submit(() -> performTask());
executor.shutdown();''',
                'tier': 25
            },
            {
                'title': 'CompletableFuture',
                'description': 'Async web-slinging',
                'code': '''CompletableFuture<String> future = CompletableFuture
    .supplyAsync(() -> fetchData())
    .thenApply(data -> process(data))
    .exceptionally(ex -> handleError(ex));''',
                'tier': 50
            }
        ]
    },
    'Shuri': {
        'name': "Shuri's Lab",
        'icon': '👑',
        'snippets': [
            {
                'title': 'ArrayList Operations',
                'description': 'Vibranium-grade collections',
                'code': '''ArrayList<String> tech = new ArrayList<>();
tech.add("Vibranium");
tech.remove(0);
boolean hasTech = tech.contains("Vibranium");''',
                'tier': 0
            },
            {
                'title': 'HashMap Storage',
                'description': 'Wakandan data vault',
                'code': '''HashMap<String, Integer> inventory = new HashMap<>();
inventory.put("Vibranium", 100);
int amount = inventory.getOrDefault("Vibranium", 0);''',
                'tier': 0
            },
            {
                'title': 'LinkedList Queue',
                'description': 'Process tech upgrades in order',
                'code': '''LinkedList<Task> queue = new LinkedList<>();
queue.offer(new Task("Upgrade"));
Task next = queue.poll();''',
                'tier': 25
            },
            {
                'title': 'TreeMap Sorted',
                'description': 'Organized royal archives',
                'code': '''TreeMap<Integer, String> sorted = new TreeMap<>();
sorted.put(1, "First");
sorted.put(3, "Third");
// Automatically sorted by key''',
                'tier': 50
            }
        ]
    },
    'Yoda': {
        'name': "Yoda's Wisdom",
        'icon': '🧙‍♂️',
        'snippets': [
            {
                'title': 'Basic Recursion',
                'description': 'The Force flows through calls',
                'code': '''public int factorial(int n) {
    if (n <= 1) return 1;  // Base case, it is
    return n * factorial(n - 1);  // Recursive, the Force is
}''',
                'tier': 0
            },
            {
                'title': 'Tree Traversal',
                'description': 'Walk the Force tree',
                'code': '''public void traverse(Node node) {
    if (node == null) return;  // Empty, the path is
    System.out.println(node.value);
    traverse(node.left);   // Left, we go
    traverse(node.right);  // Right, we go
}''',
                'tier': 25
            },
            {
                'title': 'Fibonacci Sequence',
                'description': 'Ancient pattern of numbers',
                'code': '''public int fibonacci(int n) {
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}''',
                'tier': 50
            }
        ]
    },
    'Wednesday Addams': {
        'name': "Wednesday's Evidence",
        'icon': '🖤',
        'snippets': [
            {
                'title': 'If-Else Logic',
                'description': 'Dissect the truth',
                'code': '''if (isSuspicious) {
    investigate();
} else if (isInnocent) {
    dismiss();
} else {
    observe();
}''',
                'tier': 0
            },
            {
                'title': 'Switch Statement',
                'description': 'Classify evidence',
                'code': '''switch (evidenceType) {
    case FINGERPRINT:
        analyzePrint();
        break;
    case DNA:
        processDNA();
        break;
    default:
        log("Inconclusive");
}''',
                'tier': 25
            }
        ]
    },
    'Iron Man': {
        'name': "Iron Man's Garage",
        'icon': '⚡',
        'snippets': [
            {
                'title': 'Singleton Pattern',
                'description': 'One arc reactor to rule them all',
                'code': '''public class ArcReactor {
    private static ArcReactor instance;
    
    private ArcReactor() {}
    
    public static ArcReactor getInstance() {
        if (instance == null) {
            instance = new ArcReactor();
        }
        return instance;
    }
}''',
                'tier': 0
            },
            {
                'title': 'Factory Pattern',
                'description': 'Build suits on demand',
                'code': '''public class SuitFactory {
    public static Suit createSuit(String type) {
        switch(type) {
            case "MARK_I": return new MarkI();
            case "MARK_II": return new MarkII();
            default: return new BaseSuit();
        }
    }
}''',
                'tier': 25
            },
            {
                'title': 'Builder Pattern',
                'description': 'Construct complex prototypes',
                'code': '''Suit suit = new Suit.Builder()
    .withReactor("Arc Reactor")
    .withWeapons("Repulsors")
    .withColor("Red and Gold")
    .build();''',
                'tier': 50
            }
        ]
    },
    'Katniss Everdeen': {
        'name': "Katniss's Survival Kit",
        'icon': '🏹',
        'snippets': [
            {
                'title': 'Array Declaration',
                'description': 'Prepare your arrows',
                'code': '''int[] arrows = new int[12];
arrows[0] = 1;
int firstArrow = arrows[0];''',
                'tier': 0
            },
            {
                'title': 'Array Iteration',
                'description': 'Count your supplies',
                'code': '''for (int i = 0; i < supplies.length; i++) {
    System.out.println(supplies[i]);
}
// Or enhanced for loop
for (String item : supplies) {
    checkSupply(item);
}''',
                'tier': 0
            },
            {
                'title': '2D Array',
                'description': 'Map the arena',
                'code': '''int[][] arena = new int[12][12];
arena[0][0] = 1;  // Cornucopia position
int position = arena[row][col];''',
                'tier': 25
            }
        ]
    },
    'Elsa': {
        'name': "Elsa's Crystalline Code",
        'icon': '❄️',
        'snippets': [
            {
                'title': 'Clean Method',
                'description': 'Freeze complexity away',
                'code': '''// Bad: Cluttered ice
public void doEverything() { /* 100 lines */ }

// Good: Crystalline clarity
public void processData() {
    validateInput();
    transformData();
    saveResults();
}''',
                'tier': 0
            },
            {
                'title': 'Meaningful Names',
                'description': 'Clear as ice',
                'code': '''// Bad: Cryptic frost
int x = 5;

// Good: Crystal clear
int maxFrozenLayersAllowed = 5;''',
                'tier': 0
            },
            {
                'title': 'Extract Method',
                'description': 'Refactor into elegant patterns',
                'code': '''// Before: Messy snow
if (user != null && user.isActive() && user.hasPermission()) {
    // do something
}

// After: Elegant ice crystal
if (isValidActiveUser(user)) {
    // do something
}

private boolean isValidActiveUser(User user) {
    return user != null && user.isActive() && user.hasPermission();
}''',
                'tier': 25
            }
        ]
    }
}

def get_persona_snippets(persona_name):
    """Get all snippets for a persona"""
    return CODE_SNIPPETS.get(persona_name, {})

def get_unlocked_snippets(persona_name, affinity):
    """Get snippets unlocked at current affinity level"""
    persona_data = CODE_SNIPPETS.get(persona_name, {})
    snippets = persona_data.get('snippets', [])
    return [s for s in snippets if s['tier'] <= affinity]