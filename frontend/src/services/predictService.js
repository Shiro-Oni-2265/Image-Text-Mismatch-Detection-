export async function predictImageTextMismatch({ imageFile, caption }) {
  if (!imageFile || !caption) {
    throw new Error("Missing payload for prediction");
  }

  const formData = new FormData();
  formData.append("imageFile", imageFile);
  formData.append("caption", caption);

  try {
    const response = await fetch("http://127.0.0.1:5000/api/predict", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    const data = await response.json();
    return {
      isMatch: data.isMatch,
      suggestedCaption: data.suggestedCaption || "",
      simScore: data.simScore,
    };
  } catch (error) {
    console.error("Error calling predict API:", error);
    throw error;
  }
}
