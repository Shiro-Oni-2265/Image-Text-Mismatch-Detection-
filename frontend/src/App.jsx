import { useEffect, useState } from "react";
import "./App.css";
import { predictImageTextMismatch } from "./services/predictService";

export default function App() {
	const [imageFile, setImageFile] = useState(null);
	const [imagePreviewUrl, setImagePreviewUrl] = useState("");
	const [caption, setCaption] = useState("");
	const [errors, setErrors] = useState({ image: "", caption: "" });
	const [isLoading, setIsLoading] = useState(false);
	const [result, setResult] = useState(null);

	useEffect(() => {
		localStorage.removeItem("itmd-auth-user");
		localStorage.removeItem("itmd-auth-accounts");
	}, []);

	useEffect(() => {
		return () => {
			if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl);
		};
	}, [imagePreviewUrl]);

	const handleImageChange = (e) => {
		const file = e.target.files?.[0];
		if (!file) return;

		if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl);
		setImageFile(file);
		setImagePreviewUrl(URL.createObjectURL(file));
		setErrors((prev) => ({ ...prev, image: "" }));
		setResult(null);
	};

	const handleCheck = async (e) => {
		e.preventDefault();

		const nextErrors = {
			image: imageFile ? "" : "Vui lòng chọn ảnh",
			caption: caption.trim() ? "" : "Vui lòng nhập mô tả",
		};
		setErrors(nextErrors);
		if (nextErrors.image || nextErrors.caption) return;

		setIsLoading(true);
		try {
			setResult(await predictImageTextMismatch({ imageFile, caption }));
		} catch {
			setResult({ isMatch: false, suggestedCaption: "" });
		} finally {
			setIsLoading(false);
		}
	};

	const handleReset = () => {
		if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl);
		setImageFile(null);
		setImagePreviewUrl("");
		setCaption("");
		setResult(null);
		setErrors({ image: "", caption: "" });
	};

	return (
		<div className="app">
			<header className="header">
				<h1>Image-Text Mismatch</h1>
				<p>Kiem tra anh va mo ta co khop nhau khong</p>
			</header>

			<main className="card">
				<form onSubmit={handleCheck}>
					<label className="upload" htmlFor="image-input">
						{imagePreviewUrl ? (
							<img src={imagePreviewUrl} alt="Anh da chon" className="preview" />
						) : (
							<span className="upload-placeholder">
								<span className="upload-icon">+</span>
								Chon anh (PNG, JPG)
							</span>
						)}
					</label>
					<input
						id="image-input"
						type="file"
						accept="image/*"
						onChange={handleImageChange}
						hidden
					/>
					{errors.image && <p className="error">{errors.image}</p>}

					<label className="label" htmlFor="caption">
						Mo ta (caption)
					</label>
					<textarea
						id="caption"
						value={caption}
						onChange={(e) => {
							setCaption(e.target.value);
							setErrors((prev) => ({ ...prev, caption: "" }));
							setResult(null);
						}}
						placeholder="Vi du: A person standing outdoors..."
						rows={3}
					/>
					{errors.caption && <p className="error">{errors.caption}</p>}

					<div className="actions">
						<button type="submit" className="btn primary" disabled={isLoading}>
							{isLoading ? "Dang phan tich..." : "Kiem tra"}
						</button>
						<button
							type="button"
							className="btn secondary"
							onClick={handleReset}
							disabled={isLoading}
						>
							Lam moi
						</button>
					</div>
				</form>

				{(result || isLoading) && (
					<section className="result" aria-live="polite">
						{isLoading ? (
							<p className="result-muted">Dang xu ly...</p>
						) : result?.isMatch ? (
							<p className="result-ok">Anh va mo ta khop nhau</p>
						) : (
							<div className="result-bad">
								<p>Anh va mo ta khong khop</p>
								{result?.suggestedCaption && (
									<p className="result-hint">
										Goi y: {result.suggestedCaption}
									</p>
								)}
							</div>
						)}
					</section>
				)}
			</main>
		</div>
	);
}
