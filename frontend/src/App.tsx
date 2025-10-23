import { useState } from "react";

function App() {
  const [status, setStatus] = useState("");
  const [backendUrl] = useState("https://liftplan-backend.onrender.com"); // update once deployed

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);

    setStatus("Generating...");

    try {
      const response = await fetch(`${backendUrl}/generate_liftplan/`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("Failed to generate PDF");

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "liftplan.pdf";
      a.click();
      window.URL.revokeObjectURL(url);
      setStatus("✅ Done! PDF downloaded.");
    } catch (err) {
      console.error(err);
      setStatus("❌ Error generating lift plan.");
    }
  };

  return (
    <div className="flex flex-col items-center gap-4 p-8 font-sans">
      <h1 className="text-2xl font-bold">Weaving Lift Plan Generator</h1>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3 items-start">
        <label>
          Tie-up CSV:
          <input type="file" name="tieup" required />
        </label>
        <label>
          Sections CSV:
          <input type="file" name="sections" required />
        </label>
        <label>
          Treadling CSV:
          <input type="file" name="treadling" required />
        </label>
        <button
          type="submit"
          className="mt-2 px-4 py-2 bg-blue-500 text-white rounded"
        >
          Generate PDF
        </button>
      </form>
      <p>{status}</p>
    </div>
  );
}

export default App;
