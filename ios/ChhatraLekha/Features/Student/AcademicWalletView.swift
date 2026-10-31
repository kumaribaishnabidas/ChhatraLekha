import SwiftUI
import CoreImage.CIFilterBuiltins

/// Digital academic credentials wallet with privacy-preserving verification tokens.
public struct AcademicWalletView: View {
    @ObservedObject var viewModel: StudentViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var selectedCredential: AcademicCredential?

    public init(viewModel: StudentViewModel) {
        self.viewModel = viewModel
    }

    public var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    // Privacy Notice Banner
                    HStack(spacing: 10) {
                        Image(systemName: "shield.lefthalf.filled")
                            .font(.title2)
                            .foregroundColor(.brandPrimary)
                        VStack(alignment: .leading, spacing: 2) {
                            Text("Privacy by Design")
                                .font(.subheadline.bold())
                                .foregroundColor(.inkPrimary)
                            Text("Verification badges use high-entropy opaque tokens. Your 12-digit APAAR ID and phone number are never exposed to public scans.")
                                .font(.caption)
                                .foregroundColor(.inkMuted)
                        }
                    }
                    .padding(14)
                    .background(Color.surfaceBackground)
                    .cornerRadius(10)
                    .overlay(RoundedRectangle(cornerRadius: 10).stroke(Color.borderLine, lineWidth: 1))
                    .padding(.horizontal, 16)

                    // Credentials List
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Verifiable Credentials")
                            .font(.headline)
                            .padding(.horizontal, 16)

                        ForEach(viewModel.credentials) { cred in
                            VStack(alignment: .leading, spacing: 10) {
                                HStack {
                                    VStack(alignment: .leading, spacing: 4) {
                                        Text(cred.title)
                                            .font(.subheadline.bold())
                                            .foregroundColor(.inkPrimary)
                                        Text(cred.issuingInstitution)
                                            .font(.caption)
                                            .foregroundColor(.inkMuted)
                                    }
                                    Spacer()
                                    Text(cred.credentialType)
                                        .font(.caption2.bold())
                                        .padding(.horizontal, 6)
                                        .padding(.vertical, 3)
                                        .background(Color.brandPrimary.opacity(0.12))
                                        .foregroundColor(.brandPrimary)
                                        .cornerRadius(4)
                                }

                                Divider()

                                HStack {
                                    VStack(alignment: .leading, spacing: 2) {
                                        Text("Issue Date")
                                            .font(.caption2)
                                            .foregroundColor(.inkMuted)
                                        Text(cred.issueDate)
                                            .font(.caption.bold())
                                            .foregroundColor(.inkPrimary)
                                    }
                                    Spacer()
                                    Button(action: {
                                        selectedCredential = cred
                                        viewModel.issueShareToken(for: cred)
                                    }) {
                                        HStack(spacing: 4) {
                                            Image(systemName: "qrcode")
                                            Text("Show QR")
                                        }
                                        .font(.caption.bold())
                                        .foregroundColor(.white)
                                        .padding(.horizontal, 12)
                                        .padding(.vertical, 6)
                                        .background(Color.brandPrimary)
                                        .cornerRadius(6)
                                    }
                                }
                            }
                            .padding(16)
                            .background(Color.surfaceBackground)
                            .cornerRadius(12)
                            .overlay(RoundedRectangle(cornerRadius: 12).stroke(Color.borderLine, lineWidth: 1))
                            .padding(.horizontal, 16)
                        }
                    }

                    if let selected = selectedCredential {
                        // QR Badge Display Card
                        VStack(spacing: 14) {
                            Text("Time-Bound Verification Badge")
                                .font(.headline)
                                .foregroundColor(.inkPrimary)

                            if let qrImage = generateQRCode(from: "https://chhatralekha.vercel.app/verify/t/\(selected.verificationToken)") {
                                Image(uiImage: qrImage)
                                    .interpolation(.none)
                                    .resizable()
                                    .scaledToFit()
                                    .frame(width: 180, height: 180)
                                    .padding(10)
                                    .background(Color.white)
                                    .cornerRadius(10)
                                    .shadow(radius: 2)
                            }

                            Text("Verification URL:")
                                .font(.caption2.bold())
                                .foregroundColor(.inkMuted)
                            Text("https://chhatralekha.vercel.app/verify/t/\(selected.verificationToken)")
                                .font(.caption2.monospaced())
                                .foregroundColor(.brandPrimary)
                                .multilineTextAlignment(.center)
                                .padding(.horizontal, 16)

                            Text("Cryptographic Seal: \(String(selected.sealHash.prefix(16)))...")
                                .font(.caption2.monospaced())
                                .foregroundColor(.inkMuted)
                        }
                        .padding(20)
                        .frame(maxWidth: .infinity)
                        .background(Color.cardBackground)
                        .cornerRadius(14)
                        .overlay(RoundedRectangle(cornerRadius: 14).stroke(Color.borderLine, lineWidth: 1))
                        .padding(.horizontal, 16)
                    }
                }
                .padding(.vertical, 16)
            }
            .navigationTitle("Academic Wallet")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }

    private func generateQRCode(from string: String) -> UIImage? {
        let context = CIContext()
        let filter = CIFilter.qrCodeGenerator()
        guard let data = string.data(using: .utf8) else { return nil }
        filter.setValue(data, forKey: "inputMessage")
        filter.setValue("M", forKey: "inputCorrectionLevel")

        guard let outputImage = filter.outputImage else { return nil }
        let transformed = outputImage.transformed(by: CGAffineTransform(scaleX: 10, y: 10))
        if let cgImage = context.createCGImage(transformed, from: transformed.extent) {
            return UIImage(cgImage: cgImage)
        }
        return nil
    }
}

