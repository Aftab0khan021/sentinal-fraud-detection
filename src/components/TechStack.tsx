import { Card } from "./ui/card";

export const TechStack = () => {
  const technologies = [
    { name: "Python 3.9+", category: "Core Language" },
    { name: "PyTorch Geometric", category: "Graph ML" },
    { name: "NetworkX", category: "Graph Processing" },
    { name: "LangChain", category: "Agent Framework" },
    { name: "Ollama", category: "Local LLM Runtime" },
    { name: "Llama3 / Mistral", category: "LLM Models" },
    { name: "Pandas", category: "Data Processing" },
    { name: "NumPy", category: "Numerical Computing" },
  ];
  
  return (
    <section className="bg-muted/30 py-20 border-t border-border">
      <div className="container mx-auto px-4">
        <div className="mx-auto max-w-5xl">
          <h2 className="text-3xl font-bold mb-4 text-center text-foreground">
            Technology Stack
          </h2>
          <p className="text-center text-muted-foreground mb-12 max-w-2xl mx-auto">
            Built with industry-standard tools for graph ML and privacy-preserving LLM applications
          </p>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {technologies.map((tech, idx) => (
              <Card key={idx} className="p-4 bg-card hover:shadow-md transition-shadow text-center">
                <p className="font-semibold text-card-foreground">{tech.name}</p>
                <p className="text-xs text-muted-foreground mt-1">{tech.category}</p>
              </Card>
            ))}
          </div>
          
          <div className="mt-12 p-6 rounded-xl border border-primary/20 bg-primary/5">
            <h3 className="font-semibold mb-2 text-foreground">🔒 Privacy-First Design</h3>
            <p className="text-sm text-muted-foreground">
              All LLM processing happens locally via Ollama. Financial data never leaves your environment—no external API calls to OpenAI or cloud services. Perfect for compliance with data protection regulations.
            </p>
          </div>
          
          <div className="mt-8 text-center">
            <p className="text-sm text-muted-foreground mb-4">
              Ready to explore the code?
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <a 
                href="https://github.com/yourusername/sentinal" 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-6 py-3 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
              >
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
                </svg>
                View on GitHub
              </a>
              <a 
                href="/docs" 
                className="inline-flex items-center justify-center gap-2 rounded-lg border border-border bg-background px-6 py-3 text-sm font-medium text-foreground hover:bg-muted transition-colors"
              >
                Read Documentation
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
