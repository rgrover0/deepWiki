import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

TEST_PROMPT = """You are a senior Java developer specializing in testing Spring Boot applications.
Generate complete test cases based on the requirement and implementation plan.

WIKI CONTEXT:
{context}

REQUIREMENT: {requirement}

IMPLEMENTATION PLAN:
{plan}

Generate tests in this exact format:

## Unit Tests (JUnit5 + Mockito)
```java
// For each affected class, generate a complete test skeleton
@ExtendWith(MockitoExtension.class)
class [ClassName]Test {{

    @Mock
    private [Dependencies];

    @InjectMocks
    private [ClassName] [instanceName];

    @Test
    void [methodName]_[scenario]_[expectedResult]() {{
        // Arrange
        
        // Act
        
        // Assert
    }}
}}
```

## Integration Tests (SpringBootTest)
```java
@SpringBootTest
@AutoConfigureMockMvc
class [ClassName]IntegrationTest {{

    @Autowired
    private MockMvc mockMvc;

    @Test
    void [scenario]_returnsExpectedResponse() throws Exception {{
        mockMvc.perform(...)
               .andExpect(status().isOk())
               .andExpect(...);
    }}
}}
```

## Test Scenarios
List all scenarios covered:
- Happy path scenarios
- Edge cases
- Error/validation scenarios

Use actual class and method names from the wiki context."""


def generate_tests(
    requirement: str,
    plan: str,
    context: str
) -> dict:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": TEST_PROMPT.format(
                context=context,
                requirement=requirement,
                plan=plan
            )
        }],
        max_tokens=1200,
        temperature=0.2
    )
    return {
        "tests":         response.choices[0].message.content.strip(),
        "prompt_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
        "total_tokens":  response.usage.total_tokens
    }